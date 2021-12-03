import boto3
import os
import time

class Client:
    def __init__(self, regiao):
        self.regiao = regiao
        self.SGid = 'default'
        if regiao == 'us-east-2':
            self.imageId = "ami-020db2c14939a8efb"
        if regiao == 'us-east-1':
            self.imageId = "ami-0279c3b3186e54acd"
            self.clientLB = boto3.client('elbv2', region_name='us-east-1')
            self.clientASG = boto3.client("autoscaling", region_name='us-east-1')
        self.client = boto3.client("ec2", region_name= self.regiao)
           

    def CreateSGs(self, GroupName, Descricao,ports ):
        self.GroupSG = GroupName
        print("criando security group \n")
        Permissoes = []
        for port in ports:
            Permissoes.append({
                "IpProtocol" : "tcp",
                "FromPort" : port,
                "ToPort" : port,
                "IpRanges" : [{"CidrIp" : "0.0.0.0/0"}]
            })
        try:
            resp_create_SG = self.client.create_security_group(Description=Descricao,GroupName=GroupName)
            self.SGid = resp_create_SG["GroupId"]
            self.client.authorize_security_group_ingress(GroupId = self.SGid, IpPermissions=Permissoes)
        except:
            print("ja existe, apagando e criando outro")
            res_delete = self.client.delete_security_group(GroupName = GroupName)
            resp_create_SG = self.client.create_security_group(Description=Descricao,GroupName=GroupName)
            self.SGid = resp_create_SG["GroupId"]
            self.client.authorize_security_group_ingress(GroupId = self.SGid, IpPermissions=Permissoes)
       
        waiter = self.client.get_waiter('security_group_exists')
        waiter.wait(GroupNames=[self.GroupSG])
        
        
        
        print("Security group criado \n")   
            

    def create_instance(self,arquivo):
        print(self.SGid)
        arquivo_lido =open(arquivo,'r').read()
        self.ip = self.client.allocate_address(Domain="standart")['PublicIp']
        print(self.ip)
        resp_create_instancia = self.client.run_instances(
            ImageId = self.imageId,
            MinCount = 1,
            MaxCount = 1,
            InstanceType = "t2.micro",
            KeyName = self.key,
            UserData= arquivo_lido,
            SecurityGroupIds   = [self.SGid],
        )
        print("Criando instancia \n")
        self.instance_id = resp_create_instancia['Instances'][0]["InstanceId"]
        self.subnetID = resp_create_instancia['Instances'][0]["NetworkInterfaces"][0]['SubnetId']
        self.VcpId = resp_create_instancia['Instances'][0]["NetworkInterfaces"][0]['VpcId']
        waiter = self.client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[self.instance_id])
        response_IP = self.client.associate_address(InstanceId = self.instance_id,PublicIp=self.ip)
        print("Instancia criada \n")


    def destroy_instance(self):
        print("Destruindo instancia \n")
        resp_destroy = self.client.terminate_instances(InstanceIds=[self.instance_id])
        waiter = self.client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=[self.instance_id])
        
        #destruir o Elastic IP Adress
        AllocationId = self.client.describe_addresses(PublicIps=[self.ip,])['Addresses'][0]['AllocationId']
        resp_releaseIP = self.client.release_address(AllocationId = AllocationId)
        
        print("instancia destruida \n")
            

    def create_AMI(self,nome):
        #Apagar imagem se ela já existe Nao consegui faze direito
        print("Criando imagem \n")
        resp_create_Ami = self.client.create_image(InstanceId = self.instance_id, Name=nome)
        self.image_id_copy = resp_create_Ami['ImageId']
        waiter = self.client.get_waiter('image_available')
        waiter.wait(ImageIds=[self.image_id_copy])
        print("Imagem Criada \n")
        #opcao = input("Deseja apagar a instância(y/n)")
        opcao = 'y'
        if opcao == 'y':
            self.destroy_instance()


    def destroy_AMI(self):
        resp_des_AMI = self.client.deregister_image(ImageId=self.image_id_copy)
        

    def create_key(self,key_name):
        print("Criando Chave")
        self.key = key_name
        try:
            response_keycreation = self.client.create_key_pair(
                KeyName = key_name,
                KeyType = 'rsa'
            )
            arquivo_pem = response_keycreation['KeyMaterial']
            diretorio_arquivo = "./"+ key_name + ".pem"
            nome_arquivo = "./"+ key_name + ".pem"
            if (os.path.isfile(nome_arquivo)):
                os.remove(nome_arquivo)
            f = open(nome_arquivo, "x")
            f.write(arquivo_pem)
            f.close()
            print("Chave Criada")
        except:
            print("Essa chave já existe, apagando-a e criando uma nova")
            response = self.client.delete_key_pair(KeyName = key_name)
            print("Chave Deletada")
            self.create_key(key_name)


    def create_LB(self,nome):
        print("Criando LB \n")
        res_subs = self.client.describe_subnets()
        sub = []
        self.aval_zone = []
        for e in res_subs['Subnets']:
            sub.append(e["SubnetId"])
            self.aval_zone.append(e["AvailabilityZone"])
        self.nomeLB = nome
        resp_lb = self.clientLB.create_load_balancer(
            Name= self.nomeLB ,
            Subnets= sub, #lista com todas as subnets disponíveis
            SecurityGroups=[
                self.SGid,
            ],
            Scheme='internet-facing',
            Type='application',
            IpAddressType='ipv4',
        )
        self.LB_ARN = resp_lb['LoadBalancers'][0]['LoadBalancerArn']
        waiter = self.clientLB.get_waiter('load_balancer_available')
        waiter.wait(LoadBalancerArns=[self.LB_ARN])
        self.DNS = resp_lb['LoadBalancers'][0]['DNSName']
        print("LB criado")
        

    def destroy_LB(self):
        response = self.clientLB.delete_load_balancer(LoadBalancerArn= self.LB_ARN)
        waiter = self.clientLB.get_waiter('load_balancers_deleted')
        waiter.wait(LoadBalancerArns=[self.LB_ARN])
        print("LoadBalancer deletado \n")
        

    def create_launch_template(self,nome):
        print("Criando launch Template")
        self.LT_name = nome
        resLauchTemplate = self.client.create_launch_template(
        LaunchTemplateName= nome,
        LaunchTemplateData = {
            'ImageId': self.image_id_copy,
            'InstanceType': 't2.micro',
            'KeyName' : self.key,
            'SecurityGroupIds': [self.SGid]
            }
        )
        self.templateId = resLauchTemplate['LaunchTemplate']['LaunchTemplateId']
        print("Launch Template criado")


    def destroy_launch_template(self):
        resp_LT_delete = self.client.delete_launch_template(LaunchTemplateName= self.LT_name)
        print("Launch Template destruido")
        

    def create_ASG(self, nome):
        self.ASG_name = nome
        resp_ASG = self.clientASG.create_auto_scaling_group(
            AutoScalingGroupName= nome,
            LaunchTemplate={
                'LaunchTemplateId': self.templateId
            },
            MinSize=1,
            MaxSize=5,
            DesiredCapacity=1,
            AvailabilityZones= self.aval_zone,
            TargetGroupARNs=[
                self.TG_ARN
            ],
            Tags=[
                {
                    'Key': 'Owner',
                    'Value': "Henrique"
                },
                {
                    'Key': 'Name',
                    'Value': "DJANGOASG"
                },
            ]
        )
        print("ASG criado \n")


    def destroy_ASG(self):
        response = self.clientASG.delete_auto_scaling_group(AutoScalingGroupName=self.ASG_name,ForceDelete=True)
        time.sleep(30)


    def create_target_group(self,name):
        resp_TG = self.clientLB.create_target_group(
            Name= name,
            Protocol='HTTP',
            Port=8080,
            VpcId=self.VcpId,
            HealthCheckProtocol='HTTP',
            HealthCheckEnabled=True,
            TargetType='instance',
            HealthCheckPath='/admin',

            IpAddressType='ipv4'
        )
        self.TG_ARN = resp_TG['TargetGroups'][0]['TargetGroupArn']
        print("Target Group Criado")


    def destroy_target_group(self):
        time.sleep(20)
        response = self.clientLB.delete_target_group(TargetGroupArn= self.TG_ARN)
        print("Target Group Destruido")


    def create_listner(self,name):
        print("Criando listner \n")
        resp_listner = self.clientLB.create_listener(
            LoadBalancerArn= self.LB_ARN,
            Protocol='HTTP',
            Port=80,

            DefaultActions=[
                {
                    'Type': 'forward',
                    'TargetGroupArn': self.TG_ARN
                    }
            ]
        )
        self.listnerARN = resp_listner['Listeners'][0]['ListenerArn']
        print("listner criado \n")
        
    def terminate(self):
        if (self.regiao == 'us-east-1'):
            #self.destroy_instance()
            self.destroy_AMI()
            self.destroy_LB()
            self.destroy_launch_template()
            self.destroy_ASG()
            self.destroy_target_group()
        else:
            self.destroy_instance()