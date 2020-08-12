# boids
Emergent behaviour of swarming agents, visualised. The approach used is taken from [this 1987 research paper](https://www.red3d.com/cwr/papers/1987/boids.html).

I also implemented a nice spatial partitioning system which increased the frame rate from 15FPS to 200FPS. How satisfying!

This is a super useful and beautifully simple technique for modelling crowd behaviour, with immediate canonical applications to simulating:
 - flocks of birds
 - shoals of fish
 - packs of animals
 - hordes of zombies
 
A cursory implementation of a "pursuit/flee" ruleset results in the ```wolfpack_boids.py``` file, where a population of red wolves pursues a blue sheep across the field
(click to see larger images)
| plain algorithm | pursuit/flee ruleset |
|:---:|:---:|
|![Boid demo](boid_demo.gif)|![Wolfpack demo](pursuit_demo.gif)
