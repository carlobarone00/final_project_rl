from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    # Nodo 1: Il tracker del Fra2mo (Fase 1 della missione)
    fra2mo_tracker_node = Node(
        package='ros2_fra2mo',
        executable='fra2mo_tracker.py', # Il nome esatto dello script
        name='fra2mo_mission_control',
        output='screen'
    )

    # Nodo 2: Il controllore del KUKA
    kuka_handler_node = Node(
        package='ros2_fra2mo',
        executable='kuka_handler.py',
        name='kuka_mission_control',
        output='screen'
    )

    return LaunchDescription([
        fra2mo_tracker_node,
        kuka_handler_node
    ])