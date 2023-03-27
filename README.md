# PathPlanning-GeneticAlgorithm
My project titled 'Global Path Planning Optimization for Mobile Robot Navigation Using Genetic Algorithm' was a submission for the course ECE 750: T33 Artificial Life: Biology and Computation.

In this project I surveyed the use of the Genetic Algorithm to solve path planning in mobile robot navigation. And implemented a multi-criteria optimization genetic algorithm in python and visualized the successful navigation from specified start to endpoint in a 2D environment within both static and dynamic obstacle maps.

The basic code for the genetic algorithm has been referred from [https://github.com/amirrassafi/pathplanning.] And the proposed algorithm has been built on top of this starter code. The evolutionary operators have been modified according to the assumptions made in the proposed algorithm. After importing the necessary python libraries, the main program is divided into several functional classes. Another important contribution to note is the introduction of dynamic obstacle shifting and modification of the genetic algorithm made to adapt to these changes.

The user interface for the visualization of is generated according to the steps listed in [https://linuxhint.com/use- pyqt-gui-builder/.] 

## How to run?

To run the code download the python files and change directory to the path. Activate the venv with required libraries and run as follows:

```
cd Path_to_files
source venv/bin/activated
python genetic_path_planning.py
```
The list of libraries used are updated in requirements.txt file.

## Output:

At the start of the simulation, the GUI map remains empty as it awaits the instructions to be inputted by the user, such as to set the obstacles, set the start and end position coordinates of the robot path and to set the number of iterations for which the algorithm is to be run. Once this information has been set and the simulation starts, the calls to appropriate genetic algorithm functions are made such that a number of chromosomes are initially generated, out of which the best chromosome containing the coordinates of the path joining the starting and ending points is calculated such that it minimizes the cost function value.

https://user-images.githubusercontent.com/106268058/228064230-f07540eb-a4b6-40f3-a62e-d4a8e15f5b83.mp4

Next, the genetic algorithm has been subjected to changes in the obstacle map, mid-simulation by introducing a new function for dynamic shifting of the obstacles. This dynamic function has been used after path generation, so that it causes the objects in the map to randomly shift their position. The number of times this change can occur can be controlled and for experimental purpose, the map has been subjected to 3 changes.

The initial map changes as soon as the first generation finishes its execution, displaying the path, that has more number of collisions with the obstacles. This collisions occur due to unforeseen changes in the map encounterd by the genetic algorithm However, the future generations simply adapt to these changes in the environment by making use of evolutionary operators designed previously and will eventually generate a path that does not collide with obstacles. 
