#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty, Float64MultiArray
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

class KukaHandler(Node):
    def __init__(self):
        super().__init__('kuka_handler_node')

        # 1. Trigger dal Fra2mo
        self.trigger_sub = self.create_subscription(Empty, '/mission/kuka_start_pick', self.trigger_callback, 10)

        # 2. Publisher per Braccio e Gripper (Visivo)
        self.kuka_cmd_pub = self.create_publisher(Float64MultiArray, '/iiwa_arm_controller/commands', 10)
        self.gripper_pub = self.create_publisher(JointTrajectory, '/gripper_controller/joint_trajectory', 10)

        # 3. NUOVO: Publisher per il "Magnete" di Gazebo (Fisico)
        self.attach_pub = self.create_publisher(Empty, '/iiwa/grasp/attach', 10)
        self.detach_pub = self.create_publisher(Empty, '/iiwa/grasp/detach', 10)
        #3.5: Aggiungo questo per il magnete del Fra2mo (che useremo per attaccare la scatola al Fra2mo una volta spostata)
        self.fra2mo_attach_pub = self.create_publisher(Empty, '/fra2mo/magnet/attach', 10)

        # 4. Completamento missione
        self.done_pub = self.create_publisher(Empty, '/mission/kuka_done', 10)

        self.get_logger().info('KUKA Handler ready! Waiting for Fra2mo...')
        self.is_working = False
        self.current_angles = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def trigger_callback(self, msg):
        if not self.is_working:
            self.get_logger().info('Starting manipulation...')
            self.is_working = True
            self.execute_pick_and_place()

    def publish_joint_angles(self, angles):
        msg = Float64MultiArray()
        msg.data = angles
        self.kuka_cmd_pub.publish(msg)
        self.current_angles = angles

    def move_slowly(self, target_angles, duration=3.0, steps=100):
        start_angles = self.current_angles
        sleep_time = duration / steps
        for i in range(steps + 1):
            fraction = i / steps 
            intermediate_angles = []
            for start, target in zip(start_angles, target_angles):
                current = start + (target - start) * fraction
                intermediate_angles.append(current)
            self.publish_joint_angles(intermediate_angles)
            time.sleep(sleep_time)

    def move_gripper(self, pos_left, pos_right):
        """
        Muove le dita visivamente usando la cinematica del file URDF.
        """
        msg = JointTrajectory()
        msg.joint_names = ['left_finger_joint', 'right_finger_joint']

        point = JointTrajectoryPoint()
        point.positions = [pos_left, pos_right]
        point.time_from_start.sec = 1
        point.time_from_start.nanosec = 0

        msg.points.append(point)
        self.gripper_pub.publish(msg)

    def execute_pick_and_place(self):
        # Spegniamo il magnete nel caso Gazebo l'abbia acceso all'avvio!
        self.get_logger().info('Be sure the box is not on the magnet...')
        self.detach_pub.publish(Empty())
        time.sleep(1.0) # Diamo tempo al simulatore di recepire il comando

        # 1. Vai sopra al pacco
        self.get_logger().info('Take the box...')
        target_1 = [0.0, 0.6, 0.0, -1.0, 0.0, 0.4, 0.0]
        self.move_slowly(target_1, duration=4.0, steps=150)
        
        # APRO IL GRIPPER AL MASSIMO (limite da URDF: 0.03)
        self.get_logger().info('Open Gripper...')
        self.move_gripper(0.03, -0.03) 
        time.sleep(1.5) 

        # 2. Scendi ad afferrare
        self.get_logger().info('Take the box...')
        target_2 = [0.0, 0.8, 0.0, -1.1, 0.0, 0.3, 0.0]
        self.move_slowly(target_2, duration=3.0, steps=100)

        # 3. CHIUDO IL GRIPPER E ATTIVO IL MAGNETE
        self.get_logger().info('Close the gripper and attach the box...')
        # Muovo visivamente le dita vicino alla scatola
        self.move_gripper(0.005, -0.005) 
        time.sleep(1.0)
        # Attivo il "magnete" di Gazebo per incollarla davvero!
        self.attach_pub.publish(Empty())
        time.sleep(0.5)

        # 4. Solleva il pacco
        self.get_logger().info('4. Lift the box...')
        target_3 = [0.0, 0.2, 0.0, -0.8, 0.0, 0.5, 0.0]
        self.move_slowly(target_3, duration=3.0, steps=100)

        # 5. Spostati sopra il Fra2mo (Lato opposto)
        self.get_logger().info('Move towards the Fra2mo...')
        target_4 = [-1.3, 0.35, 0.0, -0.85, 0.0, 0.5, 0.0] 
        self.move_slowly(target_4, duration=4.0, steps=150) 

        # 6. RILASCIO IL PACCO
        self.get_logger().info('Release the box...')
        # Spengo il "magnete" per lasciarla cadere
        self.detach_pub.publish(Empty())
        time.sleep(1)
        # 3. IL CONTATTO È AVVENUTO! Accendiamo il magnete del Fra2mo per incollarla!
        self.get_logger().info('Box dropped! Activating Fra2mo magnet...')
        self.fra2mo_attach_pub.publish(Empty())
        # Apro le dita visivamente
        self.move_gripper(0.03, -0.03) 
        time.sleep(1.0)

        # 7. Torna in posizione di riposo
        self.get_logger().info('Rest...')
        target_rest = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.move_slowly(target_rest, duration=3.0, steps=100)

        self.get_logger().info('Manipulation completed! Notifying the Fra2mo...')
        self.done_pub.publish(Empty())
        self.is_working = False

def main(args=None):
    rclpy.init(args=args)
    node = KukaHandler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrotto.')
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()