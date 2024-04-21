'''

Module:       main.py
Author:       EricRao
Created:      2024/3/6 16:02:38
Description:  Attacker

'''

# 导入模块
from vex import *

# 定义主控
brain = Brain()

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

# 角度传感器
pot = PotentiometerV2(brain.three_wire_port.g)

# 气动
pneumatic = DigitalOut(brain.three_wire_port.e)

# 提升
arm = Motor(Ports.PORT4, GearSetting.RATIO_18_1, False)

# 弹射
shoot_motor_a = Motor(Ports.PORT3, GearSetting.RATIO_6_1, False)
shoot_motor_b = Motor(Ports.PORT8, GearSetting.RATIO_6_1, False)
shoot = MotorGroup(shoot_motor_a, shoot_motor_b)

# 陀螺仪
inertial = Inertial(Ports.PORT7)

# 锁死结构电机
lock_motor = Motor(Ports.PORT5)
'''
全局变量声明
'''
speed_level = 2 # 2 -> 高速 1-> 低速
pneu_count = 0 # 记录气动执行次数
shoot_count = 0 # 记录投石执行次数
init_angle = 68 # 投石结构初始角度
back_angle = 300 # 投石结构后倾角度
xs = 0.7 # x轴速度
ys = 1.0 # y轴速度

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
GUI
'''
class ButtonUi:
    class Button:
        def __init__(self):
            # 初始化参数
            self.index = 0
            self.xpos = 0
            self.ypos = 0
            self.width = 80
            self.height = 80
            self.color = Color.WHITE
            self.text = ''
            self.alttext = ''
            self.state = False
            self.toggle = False
            self.callback = None

        # 开关式按钮
        def set_toggle(self, toggle, text):
            self.toggle = toggle
            if text is not None:
                self.alttext = text
            else:
                self.alttext = self.text
            return self

        # 设置按钮大小
        def set_size(self, width, height):
            self.width = width
            self.height = height
            return self

        # 设置按钮颜色
        def set_color(self, color):
            self.color = color
            return self
    
    def __init__(self):
        self.brain = Brain()
        self._buttons = []
        self._enabled = True
        self.brain.screen.pressed(self._screen_press)
        self.brain.screen.released(self._screen_release)

    @staticmethod
    # 按钮查找函数
    def _find_button(b, xpos, ypos):
        if xpos < b.xpos or xpos > (b.xpos + b.width):
            return False

        if ypos < b.ypos or ypos > (b.ypos + b.height):
            return False

        return True

    # 按钮绘制函数
    def _draw_button(self, b, bHighlight):
        if bHighlight:
            self.brain.screen.draw_rectangle(
                b.xpos, b.ypos, b.width, b.height, Color(0x808080))
        else:
            self.brain.screen.draw_rectangle(
                b.xpos, b.ypos, b.width, b.height, b.color)

        self.brain.screen.draw_rectangle(
            b.xpos, b.ypos, b.width, b.height, Color.TRANSPARENT)
        self.brain.screen.set_fill_color(Color.BLACK)
        self.brain.screen.set_pen_color(Color.WHITE)
        self.brain.screen.set_font(FontType.MONO20)

        if b.toggle and b.state:
            text = b.alttext
        else:
            text = b.text
        # we need to add text width to python VM, this will do for now
        textwidth = len(text) * 10
        self.brain.screen.print_at(
            text, opaque=False, x=b.xpos + (b.width-textwidth)/2, y=b.ypos + b.height/2 + 10)

    # 多个按钮绘制
    def _draw_buttons(self):
        for b in self._buttons:
            self._draw_button(b, False)
    
    # 按钮按下检测
    def _screen_press(self):
        if not self._enabled:
            return

        xpos = self.brain.screen.x_position()
        ypos = self.brain.screen.y_position()

        for b in self._buttons:
            if self._find_button(b, xpos, ypos):
                if b.toggle is True:
                    b.state = not b.state
                else:
                    b.state = True

                self._draw_button(b, True)
                if b.callback is not None:
                    b.callback(b.index, b.state)
                return

    # 按钮抬起检测
    def _screen_release(self):
        if not self._enabled:
            return

        for b in self._buttons:
            if not b.toggle:
                if b.state:
                    b.state = False
                    if b.callback is not None:
                        b.callback(b.index, b.state)

        self._draw_buttons()

    # 添加按钮
    def add_button(self, x, y, text, callback):
        b = ButtonUi.Button()
        b.index = len(self._buttons)
        b.xpos = x
        b.ypos = y
        b.text = text
        b.callback = callback
        self._buttons.append(b)
        return b

    # 启用
    def enable(self):
        self._enabled = True

    # 禁用
    def disable(self):
        self._enabled = False

    # 显示按钮
    def display(self, bClearScreen=False):
        if bClearScreen:
            self.brain.screen.clear_screen()
        self._draw_buttons()

'''
GUI按钮检测
'''
def userTouchAction(index, state):
    if index == 0 and not state:
        inertial_reset()

    if index == 1 and not state:
        shoot_func()

    if index == 2 and not state:
        intake_func()

    if index == 3 and not state:
        shoot_add()

# GUI对象创建
ui = ButtonUi()

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
def set_speed_1():
    global xs, ys
    xs = 0.525
    ys = 0.75
    controller_1.screen.clear_screen()
    controller_1.screen.set_cursor(2, 10)
    controller_1.screen.print("Speed Level: 1")


def set_speed_2():
    global xs, ys
    xs = 1.0
    ys = 1.0
    controller_1.screen.clear_screen()
    controller_1.screen.set_cursor(2, 10)
    controller_1.screen.print("Speed Level: 2")


'''
遥控
'''
def driver_control():
    while True:
        y = controller_1.axis3.position() * ys
        x = controller_1.axis1.position() * xs
        if abs(y) > 10 or abs(x) > 10:
                left.set_velocity( y + x , PERCENT)
                right.set_velocity( y - x , PERCENT)
                left.spin(FORWARD)
                right.spin(FORWARD)
        else:
            left.stop()
            right.stop()
        if controller_1.buttonL1.pressing():
            intake.spin(FORWARD)
        elif controller_1.buttonL2.pressing():
            intake.spin(REVERSE)
        else:
            intake.stop()  

'''
初始化
'''
def init():
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
    shoot.set_stopping(HOLD)
    shoot.set_velocity(100,PERCENT)
    shoot_motor_a.reset_position()
    shoot_motor_b.reset_position()
    shoot_motor_a.spin(REVERSE)
    shoot_motor_b.spin(REVERSE)
    while True:
        if pot.value(PERCENT) >= init_angle:
            shoot_motor_a.stop()
            shoot_motor_b.stop()
            break
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
    brain.screen.set_cursor(9,1)
    brain.screen.print("Potentiometer...")
    wait(50, MSEC)
    brain.screen.print("READY")
    wait(2,SECONDS)
    brain.screen.clear_screen()
    brain.screen.set_cursor(1,1)
    brain.screen.print("Initialization Complete.")
    wait(2, SECONDS)
    brain.screen.clear_screen()
    
    ui.add_button(50, 20, "INERTIAL", userTouchAction).set_color(Color.RED)
    ui.add_button(150, 20, "SHOOT", userTouchAction).set_color(Color.BLUE)
    ui.add_button(250, 20, "INTAKE", userTouchAction).set_color(Color.RED)
    ui.add_button(350, 20, "LOOP", userTouchAction).set_color(Color(0x208020))
    ui.display()

'''
状态显示函数
'''
def stats():
    while True:
        brain.screen.print_at("angle: ", inertial.rotation(), x=150, y=150)
        brain.screen.print_at("heading (yaw): ", inertial.heading(), x=150, y=175)
        brain.screen.print_at("rotation sensor: ", pot.value(PERCENT), x=150, y=200)
        brain.screen.print_at("shoot_count: ", shoot_count, x=150, y=225)
'''
自动程序
'''
def auton():
    pass

'''
其他函数
'''
def shoot_func():
    brain.screen.print_at("SHOOT.", x=150, y=200)
    # 设置速度
    shoot.set_velocity(100, PERCENT)
    # 设置电机停止模式为锁死
    shoot.set_stopping(HOLD)
    # 向后旋转至所定后倾角度以触发皮筋的限度拉动整个结构移动投射
    shoot_motor_a.spin_for(REVERSE,back_angle,DEGREES)
    shoot_motor_b.spin_for(REVERSE,back_angle,DEGREES)
    # 等待一段时间防止投射未完成便开始归位初始化
    wait(350,MSEC)
    # 重新旋转归位至初始位置
    shoot_motor_a.spin(REVERSE)
    shoot_motor_b.spin(REVERSE)
    while True:
        if pot.value(PERCENT) >= init_angle:
            shoot.stop()
            break
    brain.screen.clear_screen()
    ui.display()

def shoot_add():
    # 声明全局变量
    global shoot_count
    # 按下后变量值加一以记录按键触发次数
    shoot_count += 1
    if shoot_count % 2 == 1:
        wait(10, MSEC)
        # 声明全局变量绑定成为多线程任务
        global shoot_task
        shoot_task = Thread(shoot_loop)
    else:
        # 停止多线程任务
        shoot_task.stop()
        # 设置电机停止模式为刹车
        shoot.set_stopping(BRAKE)
        shoot.stop()
        wait(2,SECONDS)
        # 重新旋转归位至初始位置
        shoot_motor_a.spin(REVERSE)
        shoot_motor_b.spin(REVERSE)
        while True:
            if pot.value(PERCENT) >= init_angle:
                shoot.set_stopping(HOLD)
                shoot.stop()
                break

def shoot_loop():
    while True:
        # 设置速度
        shoot.set_velocity(100, PERCENT)
        # 设置电机停止模式为锁死
        shoot.set_stopping(HOLD)
        # 向后旋转至所定后倾角度以触发皮筋的限度拉动整个结构移动投射
        shoot_motor_a.spin_for(REVERSE,back_angle,DEGREES)
        shoot_motor_b.spin_for(REVERSE,back_angle,DEGREES)
        # 等待一段时间防止投射未完成便开始归位初始化
        wait(350,MSEC)
        # 重新旋转归位至初始位置
        shoot_motor_a.spin(REVERSE)
        shoot_motor_b.spin(REVERSE)
        while True:
            if pot.value(PERCENT) >= init_angle:
                shoot.stop()
                break

def climb():
        shoot.set_stopping(BRAKE)
        shoot.stop()
        shoot_motor_a.spin_for(FORWARD, 1, SECONDS)
        shoot_motor_b.spin_for(FORWARD, 1, SECONDS)
        wait(2,SECONDS)
        shoot.set_velocity(10, PERCENT)
        shoot.set_stopping(HOLD)
        shoot_motor_a.spin(REVERSE)
        shoot_motor_b.spin(REVERSE)
        while True:
            if pot.value(PERCENT) >= init_angle:
                shoot.set_stopping(HOLD)
                shoot.stop()
                break
    

# 重置陀螺仪
def inertial_reset():
    inertial.reset_heading()
    inertial.reset_rotation()

def intake_func():
    intake.spin(FORWARD)
        
def lock_forward():
    lock_motor.spin_for(FORWARD, 45, DEGREES)

def lock_reverse():
    lock_motor.spin_for(REVERSE, 45, DEGREES)

'''
打包
'''
# 绑定auton函数至Vex默认自动模块中去
def vexcode_auton_function():
    auton_task_0 = Thread(auton)
    while( competition.is_autonomous() and competition.is_enabled() ):
        wait(10, MSEC)
    auton_task_0.stop()

# 绑定driver_control函数至Vex默认操纵模块中去
def vexcode_driver_function():
    control_task_0 = Thread( driver_control )
    while ( competition.is_driver_control() and competition.is_enabled() ):
        wait(10, MSEC)
    control_task_0.stop()

# 注册打包的函数
competition = Competition( vexcode_driver_function, vexcode_auton_function )
wait(15, MSEC)

'''
按键检测
'''
controller_1.buttonB.pressed(pneu_toggle)
controller_1.buttonUp.pressed(set_speed_2)
controller_1.buttonDown.pressed(set_speed_1)
controller_1.buttonLeft.pressed(lock_forward)
controller_1.buttonRight.pressed(lock_reverse)
controller_1.buttonA.pressed(shoot_add)
controller_1.buttonX.pressed(climb)

'''
初始化
'''
# 启动状态显示函数
stats_thread = Thread( stats )
# 开始初始化
init()
