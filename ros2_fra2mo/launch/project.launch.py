import os

from launch import LaunchDescription
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable, ExecuteProcess, TimerAction
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution, OrSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
# 10 5 0.10 0 0 3.14
fra2mo_aruco_node = Node(
        package='aruco_ros',
        executable='single',
        name='fra2mo_aruco_single',
        output='screen',
        parameters=[{
            'marker_id': 16,
            'marker_size': 0.2,
            # Usiamo il frame ottico che abbiamo creato apposta nel file xacro!
            'reference_frame': 'fra2mo_camera_link_optical',
            'marker_frame': 'fra2mo_aruco_marker',
            'camera_frame': 'fra2mo_camera_link_optical',
            'use_sim_time': True
        }],
        remappings=[
            ('/image', '/fra2mo/camera/image_raw'),
            ('/camera_info', '/fra2mo/camera/camera_info'),
            ('/pose', '/fra2mo_aruco_single/pose')
        ]
    )

fra2mo_aruco_node_2 = Node(
    package='aruco_ros',
    executable='single',
    name='fra2mo_aruco_second',
    output='screen',
    parameters=[{
        'marker_id': 18,
        'marker_size': 0.2,
        'reference_frame': 'fra2mo_camera_link_optical',
        'marker_frame': 'fra2mo_aruco_marker_18',
        'camera_frame': 'fra2mo_camera_link_optical',
        'use_sim_time': True
    }],
    remappings=[
        ('/image', '/fra2mo/camera/image_raw'),
        ('/camera_info', '/fra2mo/camera/camera_info'),
        ('/pose', '/fra2mo_aruco_second/pose')
    ]
)

def generate_launch_description():

    # Percorsi ai file
    models_path = os.path.join(
    get_package_share_directory('ros2_fra2mo'),
    'models'
    )
    world_file = os.path.join(get_package_share_directory('ros2_fra2mo'), "worlds", "leonardo_race_field.sdf")
    fra2mo_xacro_file = "fra2mo.urdf.xacro"
    fra2mo_xacro = os.path.join(
        get_package_share_directory('ros2_fra2mo'),
        "urdf",
        fra2mo_xacro_file
    )

    # Declare arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            'runtime_config_package',
            default_value='iiwa_description',
            description='Package with the controller\'s configuration in "config" folder. \
                         Usually the argument is not set, it enables use of a custom setup.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'controllers_file',
            default_value='iiwa_controllers.yaml',
            description='YAML file with the controllers configuration.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'description_package',
            default_value='iiwa_description',
            description='Description package with robot URDF/xacro files. Usually the argument \
                         is not set, it enables use of a custom description.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'description_file',
            default_value='iiwa.config.xacro',
            description='URDF/XACRO description file with the robot.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'prefix',
            default_value='""',
            description='Prefix of the joint names, useful for multi-robot setup. \
                         If changed than also joint names in the controllers \
                         configuration have to be updated. Expected format "<prefix>/"',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'namespace',
            default_value='/',
            description='Namespace of launched nodes, useful for multi-robot setup. \
                         If changed than also the namespace in the controllers \
                         configuration needs to be updated. Expected format "<ns>/".',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Start robot in Gazebo simulation.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'use_fake_hardware',
            default_value='true',
            description='Start robot with fake hardware mirroring command to its states.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'robot_controller',
            default_value='iiwa_arm_controller',
            description='Robot controller to start.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'robot_ip',
            default_value='192.170.10.2',
            description='Robot IP of FRI interface',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'robot_port',
            default_value='30200',
            description='Robot port of FRI interface.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'initial_positions_file',
            default_value='initial_positions.yaml',
            description='Configuration file of robot initial positions for simulation.',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'command_interface',
            default_value='position',
            description='Robot command interface [position|velocity|effort].',
        )
    )
    declared_arguments.append(
        DeclareLaunchArgument(
            'base_frame_file',
            default_value='base_frame.yaml',
            description='Configuration file of robot base frame wrt World.',
        )
    )

    # Initialize Arguments
    runtime_config_package = LaunchConfiguration('runtime_config_package')
    controllers_file = LaunchConfiguration('controllers_file')
    description_package = LaunchConfiguration('description_package')
    description_file = LaunchConfiguration('description_file')
    prefix = LaunchConfiguration('prefix')
    use_sim = LaunchConfiguration('use_sim')
    use_fake_hardware = LaunchConfiguration('use_fake_hardware')
    robot_controller = LaunchConfiguration('robot_controller')
    robot_ip = LaunchConfiguration('robot_ip')
    robot_port = LaunchConfiguration('robot_port')
    initial_positions_file = LaunchConfiguration('initial_positions_file')
    command_interface = LaunchConfiguration('command_interface')
    base_frame_file = LaunchConfiguration('base_frame_file')
    namespace = LaunchConfiguration('namespace')

    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare(description_package), 'config', description_file]
            ),
            ' ',
            'prefix:=',prefix,' ',
            'use_sim:=',use_sim,' ',
            'use_fake_hardware:=',use_fake_hardware,' ',
            'robot_ip:=',robot_ip,' ',
            'robot_port:=',robot_port,' ',
            'initial_positions_file:=',initial_positions_file,' ',
            'command_interface:=',command_interface,' ',
            'base_frame_file:=',base_frame_file,' ',
            'description_package:=',description_package,' ',
            'runtime_config_package:=',runtime_config_package,' ',
            'controllers_file:=',controllers_file,' ',
            'namespace:=',namespace,
        ]
    )

    robot_description = {'robot_description': robot_description_content}

    fra2mo_robot_description = {
    "robot_description": ParameterValue(
        Command(['xacro ', fra2mo_xacro]),
        value_type=str
    )
    }
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare(runtime_config_package),
            'config',
            controllers_file,
        ]
    )

    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, robot_controllers],
        output='both',
        namespace=namespace,
        condition=UnlessCondition(use_sim),
    )
    robot_state_pub_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=namespace,
        output='both',
        parameters=[robot_description],
    )

    fra2mo_robot_state_pub_node = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    namespace='fra2mo',
    output='screen',
    parameters=[fra2mo_robot_description, {"use_sim_time": True}],
    )

    declared_arguments.append(
    DeclareLaunchArgument(
        'gz_args',
        default_value=world_file + ' -r',
        description='Arguments for gz_sim'
    )
    )
    
    """
    export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:world_simulation_models
        Siccome il suo empty.world si richiama un ground plane e un sun, assicurati di avere tali modelli installati da qualche
        parte sul tuo pc, e metti quel percorso nella EV
    """
    gazebo = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                    'launch',
                                    'gz_sim.launch.py'])]),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items(),
            condition=IfCondition(use_sim),
    )

    fra2mo_position = [1, -0.9, 0.1, 0.5]
    iiwa_position = [0.5, 1.5, 0.51]

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', 'robot_description',
                   '-name', 'iiwa',
                   '-allow_renaming', 'true',
                   '-x', str(iiwa_position[0]),
                   '-y', str(iiwa_position[1]),
                   '-z', str(iiwa_position[2]),],
        condition=IfCondition(use_sim),
    )

    spawn_fra2mo = Node(
    package='ros_gz_sim',
    executable='create',
    output='screen',
    arguments=[
        '-topic', '/fra2mo/robot_description',
        '-name', 'fra2mo',
        '-allow_renaming', 'true',
        '-x', str(fra2mo_position[0]),
        '-y', str(fra2mo_position[1]),
        '-z', str(fra2mo_position[2]),
        '-Y', str(fra2mo_position[3]),
    ],
    condition=IfCondition(use_sim),
    )

    fra2mo_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
            '/model/fra2mo/odometry@nav_msgs/msg/Odometry@ignition.msgs.Odometry',
            '/model/fra2mo/tf@tf2_msgs/msg/TFMessage@ignition.msgs.Pose_V',
            '/lidar@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            # --- NUOVI TOPIC PER LA TELECAMERA DEL FRA2MO ---
            '/fra2mo/camera/image_raw@sensor_msgs/msg/Image@ignition.msgs.Image',
            '/fra2mo/camera/camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo',
            # NUOVI TRADUTTORI PER IL MAGNETE DEL GRIPPER (Da ROS a Gazebo)
            '/iiwa/grasp/attach@std_msgs/msg/Empty@ignition.msgs.Empty',
            '/iiwa/grasp/detach@std_msgs/msg/Empty@ignition.msgs.Empty',
            # NUOVI TRADUTTORI PER IL MAGNETE DEL FRA2MO
            '/fra2mo/magnet/attach@std_msgs/msg/Empty@ignition.msgs.Empty',
            '/fra2mo/magnet/detach@std_msgs/msg/Empty@ignition.msgs.Empty'
        ],
        output='screen'
    )

    fra2mo_odom_tf = Node(
        package='ros2_fra2mo',
        executable='dynamic_tf_publisher',
        name='odom_tf',
        parameters=[{"use_sim_time": True}]
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager',
                   [namespace, 'controller_manager']],
    )

    robot_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[robot_controller, '--controller-manager', [namespace, 'controller_manager']],
    )

    gripper_controller_spawner = Node(
    package='controller_manager',
    executable='spawner',
    arguments=['gripper_controller', '--controller-manager', [namespace, 'controller_manager']],
    )

    bridge_camera = Node(
    package='ros_ign_bridge',
    executable='parameter_bridge',
    arguments=[
        '/camera@sensor_msgs/msg/Image@ignition.msgs.Image',
        '/camera_info@sensor_msgs/msg/CameraInfo@ignition.msgs.CameraInfo',
    ],
    output='screen',
    )

# 1. Avvia il joint_state_broadcaster in simulazione (dopo lo spawn in Gazebo)
    delay_jsb_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_state_broadcaster_spawner],
        ),
        condition=IfCondition(use_sim),
    )

    # 2. Avvia il joint_state_broadcaster sul robot reale (dopo il control_node)
    delay_jsb_after_control = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=control_node,
            on_start=[joint_state_broadcaster_spawner],
        ),
        condition=UnlessCondition(use_sim),
    )

    # 3. UNIONE: Avvia sia il braccio che il gripper DOPO il joint_state_broadcaster
    delay_controllers_after_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            # Passiamo una lista con entrambi i controller!
            on_exit=[robot_controller_spawner, gripper_controller_spawner], 
        )
    )

    # ==============================================================================
    # 4. NOVITÀ: SGANCIO DELLA SCATOLA
    # ==============================================================================
    # Creiamo il comando da lanciare nel terminale
    detach_magnet_cmd = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '--once', '/iiwa/grasp/detach', 'std_msgs/msg/Empty', '{}'],
        output='screen'
    )
    detach_fra2mo_magnet_cmd = ExecuteProcess(
    cmd=['ros2', 'topic', 'pub', '--once', '/fra2mo/magnet/detach', 'std_msgs/msg/Empty', '{}'],
    output='screen'
)

    # Diciamo al sistema: "Quando il controller del gripper ha finito di caricarsi, 
    # aspetta 3 secondi (per sicurezza) e poi sgancia la scatola!"
    delay_detach_after_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=gripper_controller_spawner,
            on_exit=[
                TimerAction(
                    period=1.0,
                    actions=[detach_magnet_cmd, detach_fra2mo_magnet_cmd]
                )
            ]
        )
    )

    # Lista finale dei nodi da lanciare
    nodes = [
        gazebo,
        control_node,
        spawn_entity,
        spawn_fra2mo,                 
        robot_state_pub_node,
        fra2mo_robot_state_pub_node,  
        fra2mo_bridge,
        fra2mo_odom_tf,
        fra2mo_aruco_node,
        fra2mo_aruco_node_2,
        bridge_camera,
        # Inseriamo i nostri 3 gestori di eventi compattati
        delay_jsb_after_spawn,
        delay_jsb_after_control,
        delay_controllers_after_jsb,
        delay_detach_after_controllers
    ]
    iiwa_share = get_package_share_directory('iiwa_description')
    gz_resource_path = models_path + ':' + iiwa_share + ':' + os.environ.get('GZ_SIM_RESOURCE_PATH', '')

    return LaunchDescription(
        [SetEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=gz_resource_path)]
        + declared_arguments
        + nodes
    )