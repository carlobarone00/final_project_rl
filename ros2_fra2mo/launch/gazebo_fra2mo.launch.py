import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, FindExecutable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import TimerAction
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)

def generate_launch_description():

    # Percorsi ai file
    xacro_file_name = "fra2mo.urdf.xacro"
    xacro = os.path.join(get_package_share_directory('ros2_fra2mo'), "urdf", xacro_file_name)

    models_path = os.path.join(get_package_share_directory('ros2_fra2mo'), 'models')
    world_file = os.path.join(get_package_share_directory('ros2_fra2mo'), "worlds", "leonardo_race_field.sdf")

    iiwa_share = get_package_share_directory('iiwa_description')
    iiwa_xacro = os.path.join(iiwa_share, 'config', 'iiwa.config.xacro')
    iiwa_controllers = os.path.join(iiwa_share, 'config', 'iiwa_controllers.yaml')

    # Genera la descrizione del robot usando xacro
    robot_description_xacro = {"robot_description": ParameterValue(Command(['xacro ', xacro]),value_type=str)}

    iiwa_robot_description_xacro = {
    "robot_description": ParameterValue(
        Command([
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            iiwa_xacro,
            ' ',
            'prefix:=',
            '',
            ' ',
            'use_sim:=',
            'true',
            ' ',
            'use_fake_hardware:=',
            'true',
            ' ',
            'robot_ip:=',
            '192.170.10.2',
            ' ',
            'robot_port:=',
            '30200',
            ' ',
            'initial_positions_file:=',
            'initial_positions.yaml',
            ' ',
            'command_interface:=',
            'position',
            ' ',
            'base_frame_file:=',
            'base_frame.yaml',
            ' ',
            'description_package:=',
            'iiwa_description',
            ' ',
            'runtime_config_package:=',
            'iiwa_description',
            ' ',
            'controllers_file:=',
            'iiwa_controllers.yaml',
            ' ',
            'namespace:=',
            '/iiwa',
        ]),
        value_type=str
    )
    } 
    
    # use_sim_time_arg = DeclareLaunchArgument(
    #     'use_sim_time', default_value='true', description='Use simulation/Gazebo clock')

    # Nodo robot_state_publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description_xacro,
                    {"use_sim_time": True}
            ]
    )

    iiwa_robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='iiwa',
        parameters=[iiwa_robot_description_xacro,
                    {"use_sim_time": True}],
        output='screen'
    )

    #Publishes joint states
    iiwa_joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/iiwa/controller_manager', # Slash iniziale
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    iiwa_arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'iiwa_arm_controller',
            '--controller-manager', '/iiwa/controller_manager', # Slash iniziale
        ],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )
    
    # # Nodo joint_state_publisher
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{"use_sim_time": True}]
    )

    declared_arguments = []
    declared_arguments.append(
    DeclareLaunchArgument(
        'gz_args',
        default_value=world_file + ' -r',
        description='path to world file'
    )
    )
    
    # Gazebo simulation launch description
    gazebo_ignition = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                    'launch',
                                    'gz_sim.launch.py'])]),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items()
    )

    position = [0.0, 0.0, 0.100]
    iiwa_position = [0.5, 1.5, 0.1]

    # Define a Node to spawn the robot in the Gazebo simulation
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', 'robot_description',
                   '-name', 'fra2mo',
                   '-allow_renaming', 'true',
                    "-x", str(position[0]),
                    "-y", str(position[1]),
                    "-z", str(position[2]),]
    )

    gz_spawn_iiwa = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', '/iiwa/robot_description',
                   '-name', 'iiwa',
                   '-allow_renaming', 'true',
                   '-x', str(iiwa_position[0]),
                   '-y', str(iiwa_position[1]),
                   '-z', str(iiwa_position[2])]
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
                   '/model/fra2mo/odometry@nav_msgs/msg/Odometry@ignition.msgs.Odometry',
                   '/model/fra2mo/tf@tf2_msgs/msg/TFMessage@ignition.msgs.Pose_V',
                   '/lidar@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
                   '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
                   #'/lidar/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked'], 
        output='screen'
    )

    odom_tf = Node(
        package='ros2_fra2mo',
        executable='dynamic_tf_publisher',
        name='odom_tf',
        parameters=[{"use_sim_time": True}]
    )

    ign_clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock"],
        remappings=[
            ("/tf", "tf"),
            ("/tf_static", "tf_static"),
        ],
        output="screen",
        namespace="fra2mo"
    )

    delay_iiwa_joint_state_broadcaster = RegisterEventHandler(
    event_handler=OnProcessExit(
        target_action=gz_spawn_iiwa,
        on_exit=[iiwa_joint_state_broadcaster_spawner],
    )
    )

    delay_iiwa_arm_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=iiwa_joint_state_broadcaster_spawner,
            on_exit=[iiwa_arm_controller_spawner],
        )
    )
 
    ign = [gazebo_ignition, gz_spawn_entity, gz_spawn_iiwa]
    #ign = [gazebo_ignition, gz_spawn_entity]
    nodes_to_start = [robot_state_publisher_node, iiwa_robot_state_publisher_node, joint_state_publisher_node, *ign, delay_iiwa_joint_state_broadcaster,
    delay_iiwa_arm_controller, bridge, odom_tf, ign_clock_bridge]

    gz_resource_path = models_path + ':' + iiwa_share + ':' + os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    #gz_resource_path = models_path
    return LaunchDescription(
        [SetEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=gz_resource_path)]
        + declared_arguments
        + nodes_to_start
    )