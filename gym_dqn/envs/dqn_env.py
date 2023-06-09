import gym
from gym import error, spaces, utils
from gym.utils import seeding
import numpy as np
from scipy.spatial import distance
import cv2
from math import sqrt
from PIL import Image

class dqnEnv(gym.Env):
  metadata = {'render.modes': ['human']}
  ROBOT_VISION_DISTANCE = 2
  OBSTACLE_COLLISION_PENALTY = 100
  GOAL_REWARD = 100

  def __init__(self):
    self.colors = {"robot": (255, 175, 0),
              "goal": (0, 255, 0),
              "unseen_obstacle": (0, 0, 105),
              "seen_obstacle": (0, 0, 255)}

  def init(self, x, y, gx, gy, map_size, obstacles_x, obstacles_y):
    self.x_start = x
    self.y_start = y
    self.x = x
    self.y = y
    self.gx = gx
    self.gy = gy
    self.OBSTACLE_X = obstacles_x
    self.OBSTACLE_Y = obstacles_y
    self.NUM_OBSTACLES = len(self.OBSTACLE_X)
    self.next_state = np.zeros((self.NUM_OBSTACLES + 1,))
    self.next_state[0] = distance.euclidean((self.x, self.y), (self.gx, self.gy))
    self.size = map_size
    self.d_max = self.next_state[0]

  class Blob:
    def __init__(self, x, y):
      self.x = x
      self.y = y

  def step(self, action):

      if action == 0:
        self.move(x=1, y=1)
      elif action == 1:
        self.move(x=-1, y=-1)
      elif action == 2:
        self.move(x=-1, y=1)
      elif action == 3:
        self.move(x=1, y=-1)
      elif action == 4:
        self.move(x=1, y=0)
      elif action == 5:
        self.move(x=-1, y=0)
      elif action == 6:
        self.move(x=0, y=1)
      elif action == 7:
        self.move(x=0, y=-1)
      elif action == 8:
        self.move(x=0, y=0)

      done = False
      robot_reward = 0
      for obstacle in self.seen_obstacles:
        if self.x == obstacle.x and self.y == obstacle.y:
          robot_reward -= self.OBSTACLE_COLLISION_PENALTY
          done = True

      if not done and self.x == self.gx and self.y == self.gy:
        robot_reward += self.GOAL_REWARD
        done = True

      # check for new seen obstacles within (robot vision range)
      for obstacle in self.unseen_obstacles:
        robot_to_obstacle = distance.euclidean((self.x, self.y), (obstacle.x, obstacle.y))
        if self.ROBOT_VISION_DISTANCE >= robot_to_obstacle:
          self.seen_obstacles.append(obstacle)
          self.unseen_obstacles.remove(obstacle)
            
      robot_to_goal = distance.euclidean((self.x, self.y), (self.gx, self.gy))
      robot_reward += 0.1*(self.d_max-robot_to_goal);
        
      for i in range(0, len(self.seen_obstacles)):
        self.next_state[i+1] = distance.euclidean((self.x, self.y), (self.seen_obstacles[i].x, self.seen_obstacles[i].y))
      self.next_state[0] = distance.euclidean((self.x, self.y), (self.gx, self.gy))

      return self.next_state, robot_reward, done

  def move(self, x, y):

      self.x += x
      self.y += y

      # If we are out of bounds
      if self.x < 0:
        self.x = 0
      elif self.x > self.size-1:
        self.x = self.size-1
      if self.y < 0:
        self.y = 0
      elif self.y > self.size-1:
        self.y = self.size-1

  def reset(self):
      self.x, self.y = self.x_start, self.y_start
      self.obstacles = []
      for i in range(self.NUM_OBSTACLES):
        new_obstacle = self.Blob(self.OBSTACLE_X[i], self.OBSTACLE_Y[i])
        self.obstacles.append(new_obstacle)
      self.unseen_obstacles = self.obstacles
      self.seen_obstacles = []
      self.episode_step = 0
      self.next_state = np.zeros((self.NUM_OBSTACLES+1, ))
      self.next_state[0] = distance.euclidean((self.x, self.y), (self.gx, self.gy))

      return self.next_state

  def render(self, mode='human', close=False):
    img = self.get_image()
    img = img.resize((300, 300))
    cv2.imshow("Map", np.array(img))
    cv2.waitKey(1)

  def get_image(self):
    env = np.zeros((self.size, self.size, 3), dtype=np.uint8)  # starts an rbg of our size
    env[self.x][self.y] = self.colors["robot"]  # sets the robot tile to blue
    env[self.gx][self.gy] = self.colors["goal"]  # sets the goal location tile to green color
    for obstacle in self.unseen_obstacles:
      env[obstacle.x][obstacle.y] = self.colors["unseen_obstacle"]  # sets the obstacle locations to dark red
    for obstacle in self.seen_obstacles:
      env[obstacle.x][obstacle.y] = self.colors["seen_obstacle"]  # sets the seen obstacle locations to bright red

    img = Image.fromarray(env, 'RGB')  # reading to rgb even tho color definitions are bgr
    return img
