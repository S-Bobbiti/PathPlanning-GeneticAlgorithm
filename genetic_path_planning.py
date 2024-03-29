# The genetic algorithm for path planning has been built with inspiration from the following sources:
# https://github.com/amirrassafi/pathplanning
# https://linuxhint.com/use-pyqt-gui-builder/


from PyQt5.QtWidgets import QApplication, QMainWindow
import sys
# sys.path.insert(0, "./ui/")
from pp_ui import Ui_MainWindow
from PyQt5 import QtWidgets
import math
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.geometry import LineString
from descartes import PolygonPatch
import random,itertools
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import time
import timeit


# The below class is used to get waypoints of the path
class MyPoint(Point):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __add__(self, other):
        return MyPoint(self.x + other.x, self.y + other.y)

    def scale(self, ratio):
        return MyPoint(self.x * ratio, self.y * ratio)

    def getXy(self):
        return (self.x, self.y)

    def rotate(self, theta):
        c, s = np.cos(theta), np.sin(theta)
        r = np.array([[c, -s], [s, c]])
        new_xy = list(np.matmul(r, self.getXy()))
        return MyPoint(new_xy[0], new_xy[1])

# Line angle is calculated using coordinates of two points
class MyLineString(LineString):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def getMyAngle(self):
        return math.atan2(self.coords[1][1] - self.coords[0][1],
                          self.coords[1][0] - self.coords[0][0])

    def getAngle(self, other):
        return math.fabs(self.getMyAngle() - other.getMyAngle())%math.pi

# The random set of objects are generated and placed in map using
# the following class
class Obstacle(Polygon):

    def __init__(self, center_point, size = 1):
        self.center = center_point
        corners = [MyPoint(-1, -1), MyPoint(-1, 1), MyPoint(1, 1), MyPoint(1, -1)]
        corners = [p.scale(size) for p in corners]
        new_corners = [c+center_point for c in corners]
        self.p = Polygon([(p.x, p.y) for p in new_corners])
        super().__init__(self.p)

    def getDrawble(self, color):
        return PolygonPatch(self.p, color=color)

    def getCenter(self):
        return self.center

# Depicts the entity moving across the plane
# Contains various functions dedicated to evaluate its movement
class Robot:
    def __init__(self, start_point, end_point, grid_num, obstacles):
        self.__s_point = start_point
        self.__t_point = end_point
        self.__point_num = grid_num
        self.__obstacles = obstacles
        self.__createStLine()

    def __createStLine(self):
        self.__st_line = MyLineString([self.__s_point.getXy(), self.__t_point.getXy()])
        self.__theta = math.atan2(self.__t_point.y - self.__s_point.y,
                                  self.__t_point.x - self.__s_point.x)
        self.__x_prime_array = np.arange(0, self.__st_line.length+self.__st_line.length/self.__point_num,
                                         self.__st_line.length/self.__point_num)
        self.__points = [MyPoint(x, 0) for x in self.__x_prime_array]
        self.__lines = []

    def setStartStopPoint(self, s_point, t_point):
        self.__s_point = s_point
        self.__t_point = t_point
        self.__createStLine()

    def setObstacles(self, obstacles):
        self.__obstacles = obstacles
        
    def updatePoints(self, points):
        
        points = [0]+points+[0]
        self.__points = [MyPoint(x, y).rotate(self.__theta) for x, y in zip(self.__x_prime_array, points)]
        self.__points = [MyPoint(p.x, p.y) + self.__s_point for p in self.__points]
        self.__lines = [MyLineString([p1.getXy(), p2.getXy()]) for
                        p1, p2 in zip([self.__s_point] + self.__points,
                                      self.__points+[self.__t_point])]

    def getCost(self, points = []):
        if len(points) != 0:
            self.updatePoints(points)
        return (self.collision_num()*50 + self.robo_dist_to_obj()*20 + 3*self.path_len() + self.path_smoothness()*12)

    def collision_num(self):
        cv = 0
        for l in self.__lines:
           for obs in self.__obstacles:
                if obs.intersects(l):
                    cv = cv + 1
        return cv

    def path_len(self):
        d = 0
        for l in self.__lines:
            d = d + l.length
        return d

    def path_smoothness(self):
        angles = []
        for i in range(len(self.__lines) - 1):
            angles.append(self.__lines[i].getAngle(self.__lines[i + 1]))
        return max(angles)

    def robo_dist_to_obj(self):
        # This function can be changed according to our assumption
        min = 1000
        for l in self.__lines:
            for obs in self.__obstacles:
                if l.distance(obs) < min:
                    min = l.distance(obs)
        return  math.exp(-0.2 * min)

    # return a line from start to stop
    def get_straight_line(self):
        return self.__st_line

    def starting_point(self):
        return self.__s_point

    def ending_point(self):
        return self.__t_point

    def draw_way(self):
        return LineString([p.getXy() for p in self.__points])

    def angle(self):
        return self.__theta

    def Obstacles(self):
        return self.__obstacles

class GA:
    class Chromosome():
        def __init__(self, genes_len = 10, min=-5, max=5, genes = []):
            if len(genes) == 0:
                self.__genes = np.random.uniform(min, max, genes_len)
            else:
                self.__genes = genes

        def mutate(self, min, max):
            mutate_num = np.random.randint(0, len(self.__genes)-1, 1)
            mutate_index = np.random.randint(0, len(self.__genes)-1, mutate_num)
            new_chr = np.array(self.__genes)
            for index in mutate_index:
                new_chr[index] = np.random.uniform(min, max, 1)
            return GA.Chromosome(genes=new_chr)

        def crossOver(self, other):
            # cross_over_point
            cop = np.random.randint(0, len(self.__genes), 2)
            chr1 = np.array(self.__genes)
            chr2 = np.array(other.getGenes())
            chr1[cop[0]: cop[1]], chr2[cop[0]: cop[1]] = chr2[cop[0]: cop[1]], chr1[cop[0]: cop[1]]
            chr1[cop[0]: cop[1]] = [(x+y)/2 for x,y in zip(chr1[cop[0]: cop[1]], chr2[cop[0]: cop[1]])]
            chr2[cop[0]: cop[1]] = chr1[cop[0]: cop[1]]
            return list([GA.Chromosome(genes=chr1), GA.Chromosome(genes=chr2)])

        def getGenes(self):
            return list(self.__genes).copy()

    # get size of population and chromosome and talent size at the first
    def __init__(self, chr_size, talent_size):
        self.__chr_size = chr_size
        self.__talentSize = talent_size
        self.__population = []
        self.__top = {"cost_value": float('Inf'), "chr": []}

    def resetTop(self):
        self.__top = {"cost_value": float('Inf'), "chr": []}

    def reset(self, pop_size):
        self.cleanPopulation()
        self.genPopulation(min=-3, max=3, pop_size=pop_size)

    def cleanPopulation(self):
        self.__population = []

    def setPopulation(self, population):
        self.__population = population

    def getPopulation(self):
        return self.__population

    def appendPopulation(self, population):
        self.__population = self.__population + population

    def changePopulation(self, pop):
        del(self.__population[int(len(self.__population)/2) : ])
        self.appendPopulation(pop)

    def genPopulation(self,  max, min, pop_size):
        for p in range(pop_size):
            self.__population.append(self.Chromosome(self.__chr_size, min, max))
        return self.__population

    def mutuation(self, num, min, max):
        if num > len(self.__population):
            raise ("number of mutation is higher than population")
        mutated = []
        mutate_indexs = np.random.randint(0, len(self.__population), num)
        for mutate_index in mutate_indexs:
            mutated = mutated + [self.__population[mutate_index].mutate(min, max)]
        return mutated

    def crossOver(self, num):
        crossover_pop = []
        for i in range(num):
            s = list(np.random.randint(0, len(self.__population), 2))
            crossover_pop = crossover_pop + self.__population[s[0]].crossOver(self.__population[s[1]])
        return crossover_pop

    def calPopFitness(self, func, pop = []):
        if(len(pop)==0):
            fitness_list = [func(chr.getGenes()) for chr in self.__population]
        else:
            fitness_list = [func(chr.getGenes()) for chr in pop]
        sorted_list = sorted(zip(fitness_list, self.__population),key=lambda f:f[0])
        sorted_chromosome = [s[1] for s in sorted_list]
        top_fitness = sorted_list[0][0]
        print(top_fitness)
        if(self.__top["cost_value"] > top_fitness ):
            self.__top["cost_value"] = top_fitness
            self.__top["chr"] = sorted_list[0][1]
        return sorted_chromosome, top_fitness

    def getTop(self):
        return self.__top["chr"]

class Result:
    def __init__(self):
        self.__cost = {}

    def reset(self):
        self.__cost = {}

    def addCost(self, run_index, data):
        if not run_index in self.__cost.keys():
            self.__cost[run_index] = []
        self.__cost[run_index] = self.__cost[run_index] + data

    def getRunNumber(self):
        return len(self.__cost.keys())

    def getCost(self, run_index):
        try:
            return self.__cost[run_index]
        except:
            return []

    def getAverage(self):
        #warning return size is minumum of list
        return list(map(lambda x:sum(x)/len(x), zip(*self.__cost.values())))

    def getCosts(self):
        r = self.__cost.copy()
        r.update({len(self.__cost): self.getAverage()})
        return r


#create robot object
run_index = 1
flag = True
grid_size = 15 # 15
pop_size = 50 # 20
result_o = Result()
r = Robot(MyPoint(0, 0), MyPoint(10, 10), grid_size + 1, None)
ga = GA(chr_size = grid_size, talent_size = 3)
g = ga.genPopulation(min = -5, max = 5,pop_size=pop_size)


# Visualization functions
def addStartStopPointsToCanvas(ui, start, end):
    ui.widget.canvas.ax.plot([start.x], [start.y], 'ro', color = "blue"),
    ui.widget.canvas.ax.annotate("start", xy=(start.x, start.y), xytext = (start.x, start.y + 0.2))
    ui.widget.canvas.ax.plot([end.x], [end.y], 'ro', color = "blue")
    ui.widget.canvas.ax.annotate("end", xy=(end.x, end.y), xytext = (end.x, end.y + 0.2))

def addObstacles(ui, obstacles, color="orange"):
    for obs in obstacles:
        ui.widget.canvas.ax.add_patch(obs.getDrawble(color))

def addPath(ui, p):
    ui.widget.canvas.ax.add_line(
        mlines.Line2D([p.coords[i][0] for i in range(len(p.coords))], [p.coords[i][1] for i in range(len(p.coords))],
                      color="green"))

# Genetic algorithm
def gaIterate(num, mutate_chance=0.8, mutate_min=-15, mutate_max=15):
    global flag
    global pop_size
    cost = []
    for i in range(num):
        print("iterate", i)
        best_path, most_fit = ga.calPopFitness(r.getCost)
        cost.append(most_fit)
        ga.cleanPopulation()
        ga.setPopulation(best_path)
        cross_overed = ga.crossOver(int(pop_size / 2))
        
        if flag:
            ga.appendPopulation(cross_overed)
            flag = False
        else:
            ga.changePopulation(cross_overed)

        a = np.random.uniform(0, 1, 1)
        if (a < mutate_chance):
            mutated = ga.mutuation(pop_size, mutate_min, mutate_max)
            ga.changePopulation(mutated)
            print("mutated")
    return best_path, cost

# Function that connect to buttons of user interface
def run(ui):
    global result_o
    global pop_size
    result_o.reset()
    num_of_run = int(ui.num_of_run.text())
    for i in range(num_of_run):
        ga.reset(pop_size)
        _, cost = gaIterate(int(ui.iter_num.text()))
        result_o.addCost(i, cost)

def result(ui):
    global result_o
    print("show_result")
    costs = result_o.getCosts()
    fig, ax = plt.subplots(2, int((len(costs.keys())+1)/2))
    fig.suptitle("result")
    ax = ax.reshape(-1, 1)
    for a, i in zip(ax, range(len(costs.keys()))):
        a[0].plot(costs[i])
        a[0].grid(which='both')
        if i != len(costs.keys()) - 1:
            a[0].set_title("run" + str(i))
        else:
            a[0].set_title("ave")
    plt.show()

def set_point(ui):
    ui.widget.canvas.ax.clear()
    ui.widget.canvas.ax.grid(b=None, which='both', axis='both')
    addObstacles(ui, r.Obstacles())
    r.setStartStopPoint(MyPoint(float(ui.start_x.text()), float(ui.start_y.text())),
                        MyPoint(float(ui.end_x.text()), float(ui.end_y.text())))
    #draw
    addStartStopPointsToCanvas(ui, r.starting_point(), r.ending_point())
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    ui.widget.canvas.draw()

def generations(ui):

    t_start = time.time()
    best_path,_ = gaIterate(num=int(ui.iter_num.text()))
    r.updatePoints(list(best_path[0].getGenes()))
    p = r.draw_way()
    ui.widget.canvas.ax.clear()
    ui.widget.canvas.ax.grid(b=None, which='both', axis='both')
    addStartStopPointsToCanvas(ui, r.starting_point(), r.ending_point())
    addObstacles(ui, r.Obstacles())
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    addPath(ui, p)
    ui.widget.canvas.draw()
    t_end = time.time()

    print('Generation time: %f' %(t_end-t_start))
    print("Cost:", r.getCost())
    print("Path Length:{}".format(r.path_len()))
    print("Path Smoothness:{}".format(r.path_smoothness()))
    print("Distance to Object:{}".format(r.robo_dist_to_obj()))
    print("Number of Collisions:{}".format(r.collision_num()))
    # Uncomment below line for dynamic obstacle shift 
    # dynamic_shifting(ui) 

def dynamic_shifting(ui):
    random.seed(1)
    obstacles = [Obstacle(MyPoint(random.randint(1, 20), random.randint(1, 10)), 0.5) for i in
                 range(30)]
    r.setObstacles(obstacles)
    addObstacles(ui, obstacles)
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    ui.widget.canvas.draw()


def reset_obstacle(ui):
    global pop_size
    result_o.reset()
    ga.resetTop()
    ga.reset(pop_size)
    ui.widget.canvas.ax.clear()
    ui.widget.canvas.ax.grid(b=None, which='both', axis='both')
    random.seed(10)
    obstacles = [Obstacle(MyPoint(random.randint(1, 20), random.randint(1, 10)), 0.5) for i in
                 range(30)]
    r.setObstacles(obstacles)
    addObstacles(ui, obstacles)
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    ui.widget.canvas.draw()


def draw_best(ui):
    ui.widget.canvas.ax.clear()
    ui.widget.canvas.ax.grid(b=None, which='both', axis='both')
    r.updatePoints(list(ga.getTop().getGenes()))
    p = r.draw_way()
    print("best path cost = ", r.getCost())
    addObstacles(ui, r.Obstacles())
    addStartStopPointsToCanvas(ui, r.starting_point(), r.ending_point())
    addPath(ui, p)
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    ui.widget.canvas.draw()

def clear_path(ui):
    ui.widget.canvas.ax.clear()
    ui.widget.canvas.ax.grid(b=None, which='both', axis='both')
    addObstacles(ui, r.Obstacles())
    addStartStopPointsToCanvas(ui, r.starting_point(), r.ending_point())
    ui.widget.canvas.ax.autoscale(enable=True, axis='both', tight=None)
    ui.widget.canvas.draw()

# Ui class
class Ui(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.run.clicked.connect(lambda: run(self))
        self.reset_obstacles.clicked.connect(lambda: reset_obstacle(self))
        # self.reset_obstacles.clicked.connect(lambda: [reset_obstacle(self) for _ in range(3)])
        self.set_points.clicked.connect(lambda: set_point(self))
        self.iterate.clicked.connect(lambda: generations(self))
        self.result.clicked.connect(lambda: result(self))
        self.draw_best.clicked.connect(lambda: draw_best(self))
        self.clear_path.clicked.connect(lambda: clear_path(self))
        self.widget.canvas.ax.grid(b=None, which='both', axis='both')


# GUI application
app = QtWidgets.QApplication(sys.argv)
form = Ui()
form.show()
app.exec_()