import random
import shelve
import time
import uuid
import docker  #https://docker-py.readthedocs.io/en/stable/
import docker.errors as x
import hashlib

class PhpmyadminProvisioning:
    def __init__(self):
        #self.id = str(uuid.uuid1())
        self.dbports = shelve.open('dbports.db',writeback=True)
        self.userdb = shelve.open('users.db',writeback=True)

        #daftar mesin

        self.mesin = dict()
        self.mesin['mesin1']='tcp://192.168.99.101:2376'
        self.mesin['mesin2']='tcp://192.168.99.102:2376'
        self.mesin['mesin3']='tcp://192.168.99.103:2376'

        self.tls_config = docker.tls.TLSConfig(
            ca_cert='/home/yaniar/.docker/machine/certs/ca.pem',
            client_cert=('/home/yaniar/.docker/machine/certs/cert.pem',
                        '/home/yaniar/.docker/machine/certs/key.pem'),
            verify=True
        )

        self.mesin_terpilih = 'mesin1'

    def set_mesin(self,pilihan='mesin1'):
        self.mesin_terpilih=pilihan
        #dapat menggunakan algoritma load balancing untuk membagi beban antar mesin

    def nomor_ports_belum_dialokasikan(self,no_port=11111):
        nama_mesin = self.mesin_terpilih
        try:
            return (f"{nama_mesin}-{no_port}" in self.dbports.keys()) is False
        except:
            return True
    def find_port(self):
        nama_mesin = self.mesin_terpilih
        the_port = 11111
        gagal=5
        while True:
            the_port = random.randint(11111, 22222)
            if (self.nomor_ports_belum_dialokasikan(the_port)):
                break
            time.sleep(1)
            gagal=gagal-1
            if (gagal<0):
                raise Exception
        #self.dbports[the_port]="1"
        return the_port

    def delete(self,username='royyana'):
        self.username=username
        try:
            docker_client = docker.DockerClient(base_url=self.mesin[self.mesin_terpilih],
                                                tls=self.tls_config)

            container_mysql = docker_client.containers.get(f"{self.username}-mysql")
            container_mysql.stop()
            container_mysql.remove()


            container_phpmyadmin = docker_client.containers.get(f"{self.username}-phpmyadmin")
            container_phpmyadmin.stop()
            container_phpmyadmin.remove()


            network = docker_client.networks.get(f"{self.username}-networkbridge")
            network.remove()


            docker_client.containers.prune()
            docker_client.networks.prune()
            return dict(status="OK")
        except Exception as e:
            pass
    def get(self,username='royyana'):
        try:
            self.username = username
            info = dict(username=self.username,
                        phpmyadmin_port=self.userdb[f"{self.username}_phpmyadmin_port"],
                        mysql_port=self.userdb[f"{self.username}_mysql_port"])
            return dict(status="OK", info=info)
        except Exception as e:
            return dict(status="ERROR")

    def create(self,username='royyana'):
        self.username=username
        try:
            docker_client = docker.DockerClient(base_url=self.mesin[self.mesin_terpilih],
                                                tls=self.tls_config)
            the_port_mysql = self.find_port()
            container_mysql = docker_client.containers.run(name=f"{self.username}-mysql", image="mysql:5.7",
                                                     environment=dict(MYSQL_USER=self.username,
                                                                      MYSQL_PASSWORD=f"{self.username}-6789",
                                                                      MYSQL_ROOT_PASSWORD="mysql-4567",
                                                                      MYSQL_DATABASE=f"{self.username}-db"), ports={'3306/tcp': the_port_mysql},
                                                     detach=True)

            self.userdb[f"{self.username}_mysql"]=container_mysql.id
            self.userdb[f"{self.username}_mysql_port"]=the_port_mysql
            the_port_phpmyadmin = self.find_port()
            container_phpmyadmin = docker_client.containers.run(name=f"{self.username}-phpmyadmin", image="phpmyadmin/phpmyadmin",
                                                     environment=dict(
                                                         PMA_HOST="mysql",
                                                         PMA_PORT="3306",
                                                         PMA_USER=self.username, PMA_PASSWORD=f"{self.username}-6789",
                                                         MYSQL_ROOT_PASSWORD="mysql-4567",
                                                         PMA_PMADB=f"{self.username}-db"), ports={'80/tcp': the_port_phpmyadmin},
                                                     detach=True)
            self.userdb[f"{self.username}_phpmyadmin"]=container_phpmyadmin.id
            self.userdb[f"{self.username}_phpmyadmin_port"]=the_port_phpmyadmin



            network =docker_client.networks.create(f"{self.username}-networkbridge",driver="bridge",check_duplicate=True)
            network.connect(container_mysql,aliases=["mysql"])
            network.connect(container_phpmyadmin,aliases=["phpmyadmin"])
            self.userdb[f"{self.username}_networkbridge"]=network.id

            info = dict(username=self.username,
                        phpmyadmin_port=self.userdb[f"{self.username}_phpmyadmin_port"],
                        mysql_port=self.userdb[f"{self.username}_mysql_port"])
            return dict(status="OK",info=info)
        except Exception as e:
            return dict(status="ERROR")


def run():
    c = PhpmyadminProvisioning()
    pass
    #c.set_mesin('mesin2')
    #create resource phpmyadmin-mysql
    # info = c.create(username='royyana')

    #get resource info phpmyadmin-mysql
    #info = c.get(username='royyana')
    #c.delete(username='royyana')

if __name__=='__main__':
    run()