#!/usr/bin/env python

# Python
import copy
from random import random, randint

# ROS
from task_sim.msg import Action, Status
from task_sim.srv import QueryStatus, SelectAction
import rospy
import rospkg

from plan_network import PlanNetwork

class PlanNetworkNode:

    def __init__(self):
        """Initialize action selection from plan networks as a service in a ROS node."""
        task = rospy.get_param('~task', 'task1')
        suffix = rospy.get_param('output_suffix', '_2018-01-26')

        self.network = PlanNetwork()
        self.network.read_graph(task=task, suffix=suffix)

        self.network.test_output()

        self.service = rospy.Service('/table_sim/select_action', SelectAction, self.select_action)
        self.status_service = rospy.Service('/table_sim/query_status', QueryStatus, self.query_status)

        print 'Plan network loaded.'

    def select_action(self, req):
        """Return an action generated from the plan network."""

        action = Action()

        return action


    def query_status(self, req):
        # Check termination criteria
        completed = True
        failed = False
        status = Status()
        status.status_code = Status.IN_PROGRESS
        for object in req.state.objects:
            if object.name.lower() == 'apple':
                if not object.in_box:
                    completed = False
                else:
                    continue
                dst = sqrt(pow(20 - object.position.x, 2) + pow(1 - object.position.y, 2))
                if object.lost or dst <= 3 or dst >= 20:
                    failed = True
                    completed = False
                    break
            elif object.name.lower() == 'flashlight':
                if not object.in_drawer:
                    completed = False
                else:
                    continue
                dst = sqrt(pow(20 - object.position.x, 2) + pow(1 - object.position.y, 2))
                if object.lost or dst <= 3 or dst >= 20:
                    failed = True
                    completed = False
                    break
            elif object.name.lower() == 'batteries':
                if not object.in_drawer:
                    completed = False
                else:
                    continue
                dst = sqrt(pow(20 - object.position.x, 2) + pow(1 - object.position.y, 2))
                if object.lost or dst <= 3 or dst >= 20:
                    failed = True
                    completed = False
                    break
        if req.state.drawer_opening > 0:
            completed = False
        if req.state.lid_position.x != req.state.box_position.x or req.state.lid_position.y != req.state.box_position.y:
            completed = False

        if failed:
            status.status_code = Status.FAILED
            return status
        if completed:
            status.status_code = Status.COMPLETED
            return status

        # Check if intervention is required (state repeated 8 times in last 50 actions)
        self.state_history.append(copy.deepcopy(req.state))
        self.state_history = self.state_history[-50:]
        repeat = 0
        for state in self.state_history:
            if self.equivalent_state(state, req.state):
                repeat += 1
        if repeat >= 8:
            status.status_code = Status.INTERVENTION_REQUESTED
            # Clear state history for next intervention
            self.state_history = []

        return status

    def equivalent_state(self, s1, s2):
        return s1.objects == s2.objects and s1.drawer_position == s2.drawer_position \
               and s1.drawer_opening == s2.drawer_opening and s1.box_position == s2.box_position \
               and s1.lid_position == s2.lid_position and s1.gripper_position == s2.gripper_position \
               and s1.gripper_open == s2.gripper_open and s1.object_in_gripper == s2.object_in_gripper

if __name__ == '__main__':
    rospy.init_node('plan_network_node')

    plan_network_node = PlanNetworkNode()
    print 'Ready to generate actions.'

    rospy.spin()
