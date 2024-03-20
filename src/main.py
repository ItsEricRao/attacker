'''

Module:       main.py
Author:       EricRao
Created:      2024/3/6 16:02:38
Description:  Attacker

'''

# 导入模块
from vex import *

# 定义主控
brain=Brain()

'''
全局变量声明
'''
speed_level = 2 # 2 -> 高速 1-> 低速
pneu_count = 0 # 记录气动执行次数


'''
端口配置
'''
# 右电机
right_motor_a = Motor(Ports.PORT1, GearSetting.RATIO_6_1, False)
right_motor_b = Motor(Ports.PORT2, GearSetting.RATIO_6_1, True)
right = MotorGroup(right_motor_a, right_motor_b)

# 收集（电机）
intake = Motor(Ports.PORT11, GearSetting.RATIO_18_1, True)

# 左电机
left_motor_a = Motor(Ports.PORT10, GearSetting.RATIO_6_1, True)
left_motor_b = Motor(Ports.PORT9, GearSetting.RATIO_6_1, False)
left = MotorGroup(left_motor_a, left_motor_b)

# 控制器
controller_1 = Controller(PRIMARY)

# 电位器
pot = PotentiometerV2(brain.three_wire_port.g)

# 气动
pneumatic = DigitalOut(brain.three_wire_port.e)

# 提升
arm = Motor(Ports.PORT4, GearSetting.RATIO_18_1, False)

# 弹射
shoot_motor_a = Motor(Ports.PORT3, GearSetting.RATIO_36_1, False)
shoot_motor_b = Motor(Ports.PORT8, GearSetting.RATIO_36_1, True)
shoot = MotorGroup(shoot_motor_a, shoot_motor_b)

# 陀螺仪
inertial = Inertial(Ports.PORT7)

# 等待初始化
wait(30, MSEC)

'''
载具控制
'''
class Vehicle():
    '''
    初始化
    '''
    def __init__(self, kp_move = 0.115, ks_move = 2):
        # 方向
        self.direction = self.output_angle = 0
        
        self.kp_angle = 0.68
        self.ks_angle = 1.5
        self.kp_move = kp_move
        self.ks_move = ks_move
    
    '''
    转向控制
    '''
    def turn_angle(self,rotation_angle):
        self.direction = rotation_angle 
        while True:
            self.output_angle = rotation_angle - inertial.rotation(DEGREES)
            if self.output_angle > 0:
                self.ks_angle = abs(self.ks_angle)
            elif  self.output_angle < 0:
                self.ks_angle = -abs(self.ks_angle)
            else:
                self.ks_angle = 0
            self.output_velocity = self.output_angle * self.kp_angle + self.ks_angle
            if self.output_velocity > 80 :
                self.output_velocity = 80 
            left.set_velocity(self.output, PERCENT)
            right.set_velocity(-self.output, PERCENT)

            left.spin(FORWARD)
            right.spin(FORWARD)

            if abs(self.output_angle) < 1:
                break

        # 停止总电机组
        left.stop()
        right.stop()

    '''
    移动底盘
    '''
    def move(self,code):     
        left.set_position(0,DEGREES)
        right.set_position(0,DEGREES)
        while True:
            self.output_angle = code - left.position(DEGREES)
            if self.output_angle > 0:
               self.ks_move = abs(self.ks_move)
            elif self.output_angle < 0:
                self.ks_move = -abs(self.ks_move)
            self.output = self.output_angle * self.kp_move + self.ks_move
            if self.output > 80:
                self.output = 80 
            left.set_velocity(self.output + (self.direction - inertial.rotation(DEGREES))*0.5, PERCENT)
            right.set_velocity(self.output - (self.direction - inertial.rotation(DEGREES)) *0.5, PERCENT)
   
            left.spin(FORWARD)
            right.spin(FORWARD)
            
            if abs(self.output_angle) < 2 :
                break
            wait(5,MSEC)

        left.stop()
        right.stop()
      
        self.turn_angle(self.direction)

    '''
    按时间间隔移动底盘
    '''

    def move_time(self,sec = 0.7):
        left.set_velocity(40, PERCENT)
        right.set_velocity(40, PERCENT)
  
        left.spin(FORWARD)
        right.spin(FORWARD)

        wait(sec, SECONDS)
        left.stop()
        right.stop()

    '''
    按设定角度移动底盘
    '''
    def move_angle(self,c,v = 60):
        left.set_position(0,DEGREES)
        right.set_position(0,DEGREES)
        left.set_velocity(v + (self.direction - inertial.rotation(DEGREES))*0.3, PERCENT)
        right.set_velocity(v - (self.direction - inertial.rotation(DEGREES)) *0.3, PERCENT)
       
        left.spin_for(FORWARD,c,DEGREES,wait=False)
        right.spin_for(FORWARD,c,DEGREES,wait=False) 
       
            
        left.stop()
        right.stop()
       
        self.turn_angle(self.direction)


'''
开关气动结构
'''
def pneu_toggle():
    global pneu_count
    pneu_count += 1
    if pneu_count % 2 == 1 :
        pneumatic.set(True)
    else:
        pneumatic.set(False)

'''
设置速度
'''
def set_speed(value):
    global speed_level
    speed_level = value

'''
弹射结构初始化
'''
# def shoot_ready():
#     shoot.set_stopping(HOLD)
#     while pot.angle(PERCENT) < 48:
#         shoot.spin(FORWARD)
#     shoot.stop()

'''
遥控
'''
def control():
    global shoot_ready,speed_level
    speed_level = 3
    xs = 0.7
    ys = 1.0
    while True :
        # 速度判断
        if speed_level == 2 :
            xs = 0.7
            ys = 1.0
            controller_1.screen.clear_screen()
            controller_1.screen.set_cursor(2, 10)
            controller_1.screen.print("Speed Level: 2")
        elif speed_level == 1 :
            xs = 0.3
            ys = 0.6
            controller_1.screen.clear_screen()
            controller_1.screen.set_cursor(2, 10)
            controller_1.screen.print("Speed Level: 1")
        
        # 弹射
        if controller_1.buttonR2.pressing():
            shoot.set_stopping(HOLD)
            shoot.spin(FORWARD)
        else:
            shoot.stop()

        # 底盘
        y = controller_1.axis3.position() * ys
        x = controller_1.axis1.position() * xs
        if abs(y) > 10 or abs(x) > 10 :
            left.set_velocity( y + x , PERCENT)
            right.set_velocity( y - x , PERCENT)
          
            left.spin(FORWARD)
            right.spin(FORWARD)
           
        else :
            left.stop()
            right.stop()
            
        
        # 收集结构
        if controller_1.buttonL1.pressing():
            intake.spin(FORWARD)
        elif controller_1.buttonL2.pressing():
            intake.spin(REVERSE)
        else:
            intake.stop()        

        # 提升
        if controller_1.buttonRight.pressing():
            arm.spin(FORWARD)
        elif controller_1.buttonLeft.pressing():
            arm.spin(REVERSE)
        else:
            arm.stop()

        # 弹射
        if controller_1.buttonR1.pressing():
            shoot.set_stopping(HOLD)
            shoot.set_timeout(0.5,SECONDS)
            shoot.spin_for(FORWARD,200,DEGREES)
            shoot.stop()
            shoot_ready()

        wait(5,MSEC)

'''
初始化
'''
def init():
    global shoot_ready
    brain.screen.set_cursor(1,1)
    brain.screen.print("-=Lianyungang Senior High School=- Attacker v0.1")
    wait(1, SECONDS)
    left.set_stopping(BRAKE)
    brain.screen.set_cursor(2,1)
    brain.screen.print("Left Motor...")
    wait(50, MSEC)
    brain.screen.print("READY")
    right.set_stopping(BRAKE)
    brain.screen.set_cursor(3,1)
    brain.screen.print("Right Motor...")
    wait(50, MSEC)
    brain.screen.print("READY")
    intake.set_stopping(BRAKE)
    brain.screen.set_cursor(4,1)
    brain.screen.print("Intake...")
    wait(50, MSEC)
    brain.screen.print("READY")
    shoot.set_stopping(HOLD)
    brain.screen.set_cursor(5,1)
    brain.screen.print("Catapult...")
    wait(50, MSEC)
    brain.screen.print("READY")
    arm.set_stopping(COAST)
    brain.screen.set_cursor(6,1)
    brain.screen.print("Mechanical Arm...")
    wait(50, MSEC)
    brain.screen.print("READY")
    pneumatic.set(False)
    brain.screen.set_cursor(7,1)
    brain.screen.print("Pneumatic...")
    wait(50, MSEC)
    brain.screen.print("READY")
    shoot.set_velocity(90,PERCENT)   
    shoot.set_max_torque(100,PERCENT)
    intake.set_velocity(100,PERCENT)
    arm.set_velocity(100,PERCENT)
    inertial.calibrate()
    brain.screen.set_cursor(8,1)
    brain.screen.print("Inertial...")
    wait(50, MSEC)
    brain.screen.print("READY")
    wait(2,SECONDS)
    brain.screen.clear_screen()
    brain.screen.set_cursor(1,1)
    brain.screen.print("Initialization Complete.")

'''
自动程序
'''
def auton():
    pass

def shoot_func():
    brain.screen.clear_screen()
    brain.screen.set_cursor(1,1)
    brain.screen.print("SHOOT.")
    shoot.spin(FORWARD)

'''
打包
'''
def vex_auton():
    auton_task_0 = Thread(auton)
    while( competition.is_autonomous() and competition.is_enabled() ):
        wait(10, MSEC)
    auton_task_0.stop()

def vex_control():
    control_task_0 = Thread( control )
    while ( competition.is_driver_control() and competition.is_enabled() ):
        wait(10, MSEC)
    control_task_0.stop()

# 注册打包的函数
competition = Competition( vex_auton, vex_control )
wait(15, MSEC)

'''
按键检测
'''
controller_1.buttonB.pressed(pneu_toggle)
controller_1.buttonUp.pressed(set_speed(2))
controller_1.buttonDown.pressed(set_speed(1))
controller_1.buttonA.pressed(shoot_func)

'''
初始化
'''
init()

