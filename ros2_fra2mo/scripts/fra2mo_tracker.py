#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
from std_msgs.msg import Empty
import time
import math

class Fra2moTracker(Node):
    def __init__(self):
        super().__init__('fra2mo_tracker_node')

        # --- PARAMETRI ---
        self.target_distance = 0.45
        self.z_tolerance = 0.05
        self.x_tolerance = 0.05

        # Parametri rotazione iniziale sotto il KUKA
        self.rotation_speed = 0.5               # rad/s
        self.rotation_duration = (math.pi /2) / 0.5 # ~180°
        self.rotation_start_time = None

        # Parametri avanzamento prima della ricerca del secondo tag
        self.forward_speed = 0.15
        self.forward_duration = 2.0
        self.forward_start_time = None

        # Publisher per far muovere il robot
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # Publisher per inviare il segnale al KUKA
        self.kuka_trigger_pub = self.create_publisher(Empty, '/mission/kuka_start_pick', 10)

        # Subscriber: KUKA ha finito
        self.kuka_done_sub = self.create_subscription(
            Empty,
            '/mission/kuka_done',
            self.kuka_done_callback,
            10
        )

        # Subscriber per ArUco
        self.aruco_sub = self.create_subscription(
            PoseStamped,
            '/fra2mo_aruco_single/pose',
            self.aruco_callback,
            10
        )

        self.aruco_sub_2 = self.create_subscription(
            PoseStamped,
            '/fra2mo_aruco_second/pose',
            self.aruco_callback_2,
            10
        )

        self.aruco_pose = None
        self.aruco_pose_2 = None
        self.last_msg_time = 0.0

        # Stati missione
        self.mission_state = "APPROACHING_FIRST_TAG"

        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('Started mission: Find the first tag...')

    def aruco_callback(self, msg):
        self.aruco_pose = msg
        self.last_msg_time = time.time()
    def aruco_callback_2(self, msg):
        self.aruco_pose_2 = msg
        self.last_msg_time = time.time()

    def kuka_done_callback(self, msg):
        if self.mission_state == "WAITING_FOR_KUKA":
            self.get_logger().info('KUKA finished. Moving forward before searching second tag...')
            self.aruco_pose = None
            self.forward_start_time = time.time()
            self.mission_state = "SECOND_TAG_FORWARD"

    def control_loop(self):
        current_time = time.time()
        twist = Twist()

        # --------------------------------------------------
        # STATO: attesa che il KUKA finisca
        # --------------------------------------------------
        if self.mission_state == "WAITING_FOR_KUKA":
            return

        # --------------------------------------------------
        # STATO: rotazione di 180° sotto il KUKA
        # --------------------------------------------------
        if self.mission_state == "ROTATING":
            elapsed = current_time - self.rotation_start_time

            if elapsed < self.rotation_duration:
                twist.angular.z = self.rotation_speed
                self.cmd_vel_pub.publish(twist)
                self.get_logger().info('Rotating for the placement...', throttle_duration_sec=1.0)
            else:
                self.cmd_vel_pub.publish(Twist())
                self.get_logger().info('Rotation completed! Triggering KUKA...')
                self.kuka_trigger_pub.publish(Empty())
                self.mission_state = "WAITING_FOR_KUKA"
                self.get_logger().info('Waiting for KUKA box...')
            return

        # STATO: piccolo avanzamento prima della seconda ricerca

        if self.mission_state == "SECOND_TAG_FORWARD":
            elapsed = current_time - self.forward_start_time

            if elapsed < self.forward_duration:
                twist.linear.x = self.forward_speed
                self.cmd_vel_pub.publish(twist)
                self.get_logger().info('Moving forward...', throttle_duration_sec=1.0)
            else:
                self.cmd_vel_pub.publish(Twist())
                self.aruco_pose = None
                self.mission_state = "SEARCHING_SECOND_TAG"
                self.get_logger().info('Now searching for second tag...')
            return

        # --------------------------------------------------
        # STATO: ricerca del secondo tag
        # --------------------------------------------------
        if self.mission_state == "SEARCHING_SECOND_TAG":
            if self.aruco_pose_2 is None or (current_time - self.last_msg_time > 1.0):
                twist.angular.z = 0.3
                self.cmd_vel_pub.publish(twist)
                self.get_logger().info('Searching second tag...', throttle_duration_sec=2.0)
                return
            else:
                self.get_logger().info('Second tag detected! Approaching...')
                self.mission_state = "APPROACHING_SECOND_TAG"
                return
        # STATO: avvicinamento al secondo tag
        if self.mission_state == "APPROACHING_SECOND_TAG":
            if self.aruco_pose_2 is None or (current_time - self.last_msg_time > 1.0):
                self.get_logger().info('Lost second tag. Searching again...', throttle_duration_sec=1.0)
                twist.angular.z = 0.3
                self.cmd_vel_pub.publish(twist)
                self.mission_state = "SEARCHING_SECOND_TAG"
                return

            dist_error = self.aruco_pose_2.pose.position.z - self.target_distance
            lat_error = -self.aruco_pose_2.pose.position.x

            if abs(dist_error) < self.z_tolerance and abs(lat_error) < self.x_tolerance:
                self.cmd_vel_pub.publish(Twist())
                self.get_logger().info('Second tag reached! Ready for drop-off.')
                return

            v_x = 0.5 * dist_error
            w_z = 1.0 * lat_error

            twist.linear.x = max(min(v_x, 0.3), -0.3)
            twist.angular.z = max(min(w_z, 0.5), -0.5)

            self.get_logger().info(
                f'Approaching second tag -> Err_Dist(Z): {dist_error:.2f}m, Err_Lat(X): {lat_error:.2f}m',
                throttle_duration_sec=1.0
            )
            self.cmd_vel_pub.publish(twist)
            return

        # --------------------------------------------------
        # STATO: prima missione, ricerca primo tag
        # --------------------------------------------------
        if self.mission_state == "APPROACHING_FIRST_TAG":
            if self.aruco_pose is None or (current_time - self.last_msg_time > 1.0):
                self.get_logger().info('Currently finding the first tag...', throttle_duration_sec=2.0)
                twist.linear.x = 0.0
                twist.angular.z = 0.3
                self.cmd_vel_pub.publish(twist)
                return

            dist_error = self.aruco_pose.pose.position.z - self.target_distance
            lat_error = -self.aruco_pose.pose.position.x

            if abs(dist_error) < self.z_tolerance and abs(lat_error) < self.x_tolerance:
                self.get_logger().info('Perfect position reached! Starting 180 deg rotation...')
                self.cmd_vel_pub.publish(Twist())
                self.rotation_start_time = time.time()
                self.mission_state = "ROTATING"
                return

            v_x = 0.5 * dist_error
            w_z = 1.0 * lat_error

            twist.linear.x = max(min(v_x, 0.3), -0.3)
            twist.angular.z = max(min(w_z, 0.5), -0.5)

            self.get_logger().info(
                f'Approaching first tag -> Err_Dist(Z): {dist_error:.2f}m, Err_Lat(X): {lat_error:.2f}m',
                throttle_duration_sec=1.0
            )
            self.cmd_vel_pub.publish(twist)
            return

def main(args=None):
    rclpy.init(args=args)
    node = Fra2moTracker()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrotto dall\'utente. Fermo il robot...')
        node.cmd_vel_pub.publish(Twist())
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()