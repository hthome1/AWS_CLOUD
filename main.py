from client import Client
import os
import time



start = time.time()
#Cliente Ohio
cliente1 = Client("us-east-2")
portas = [22,8080,80,5432]
cliente1.create_key("KeyCLientOhio")
cliente1.CreateSGs("SG_client1","security key do cliente 1",portas)
cliente1.create_instance("postgrees_setup.sh")


#Cliente North Virginia
clienteNV = Client("us-east-1")
portasnv = [22,8080,80]
clienteNV.create_key("KeyClienteNV")
clienteNV.CreateSGs("SG_clienteNV","security key do cliente2",portasnv)


#Mudando o arquivo de setUp
install_ORM =open("ORM_setUp.sh",'r').read()
install_ORM = install_ORM.replace("IP_CERTO",cliente1.ip)
try:
    f = open("ORM_Setup_pronto.sh", "x")
    f.write(install_ORM)
    f.close()
except:
    os.remove("ORM_Setup_pronto.sh")
    f = open("ORM_Setup_pronto.sh", "x")
    f.write(install_ORM)
    f.close()


clienteNV.create_instance("ORM_Setup_pronto.sh")
clienteNV.create_AMI("ImagemDjangoORM")
clienteNV.create_launch_template("TemplateClientNV")
clienteNV.create_target_group("TargetGroupNV")
clienteNV.create_LB("LBApplication")
clienteNV.create_ASG("ASGClienteNV")
clienteNV.create_listner("ListnerNV")
end = time.time()

DNS = clienteNV.DNS

print("O DNS eh: ", DNS)

elapsed_time = end -start

print("------------------------- \n")
print("tempo foi de ", elapsed_time/60 )
print("------------------------- \n")

final = True
while final:
    x = input("Deseja acabar com a infraestrutura? (y/n)")
    if x == "y":
        cliente1.terminate()
        clienteNV.terminate()
        final = False
        
