# 🤖 Final Project RL – Multi-Robot Interaction (KUKA + Fra2mo)

This project implements a cooperative robotic task in a simulated environment using ROS 2 and Gazebo.
A mobile robot (Fra2mo) interacts with a robotic arm (KUKA iiwa) to pick and transport an object to a target location using ArUco-based perception.

---

## 📦 Repository Setup

First, clone the repository:

```
git clone https://github.com/carlobarone00/final_project_rl.git
```

---

## 🌍 Environment Configuration

After cloning, you must export the Gazebo resource path so that models can be correctly loaded:

```
export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:/home/user/ros2_ws/install/ros2_fra2mo/share/ros2_fra2mo/worlds/models
```

---

## 🔧 Build the Workspace

Navigate to your ROS 2 workspace and build the project:

```
colcon build
```

Then source the workspace:

```
. install/setup.bash
```

---

## 🚀 Launch the Simulation

To spawn the two robots (Fra2mo + KUKA) and the Gazebo world, run:

```
ros2 launch ros2_fra2mo project.launch.py use_sim:=true
```

This will:

* Start Gazebo
* Spawn the KUKA manipulator
* Spawn the Fra2mo mobile robot
* Load the environment with ArUco markers and objects

---

## 🎯 Execute the Mission

Once the simulation is running, launch the mission:

```
ros2 launch ros2_fra2mo mission.launch.py
```

### Mission Overview

* The Fra2mo robot searches for an ArUco marker
* It approaches the KUKA robot
* KUKA picks up the object and places it on Fra2mo
* Fra2mo rotates and navigates toward a second target marker
* The object is delivered to a destination area
---

## 🎥 Demo Video

You can watch a full demonstration of the project here:

👉 https://www.youtube.com/watch?v=zCxGyRT_5zA

---
