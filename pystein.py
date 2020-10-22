import pyxel
from math import sin, cos, tan, pi, floor, ceil, sqrt

# Simple Wolfenstein-style software raytracer!
WIDTH  = 240
HEIGHT = 180

# The vertical line on the screen where
# walls that were infinitely far away would
# disappear towards.
horizon = 120

# SCALE OF THE MINIMAP!
scale  = 2

draw_FOV = False

tiles = {
    "#": 1, # Wall
    " ": 15, # Floor
}


with open("map.txt", "r") as f:
    level = []
    for line in f.readlines():
        row = [tiles[ch] for ch in line if ch != "\n"]
        level.append(row)

with open("wall.txt", "r") as f:
    bricks = []
    for line in f.readlines():
        row = [int(ch) for ch in line if ch != "\n"]
        bricks.append(row)


def wall(x, y):
    return level[y][x] == tiles['#'];

# Player position
X, Y = (4, 4)
# Player size (player is a square)
R = 1/4

# angle between player face and x-axis
phi = 0

# FOV in degrees because that is what people usually tihnk about
FOV = 60

# FOV in radians because math
FOV_rad = FOV * pi / 180

def left_extreme(phi):
    return phi - FOV_rad / 2

# Epsilon is the angle betweeen rays.
epsilon = FOV_rad / WIDTH


def walk(dx, dy):
    global Y

    if dx < 0:
        walk_w(-dx)
    
    if dx > 0:
        walk_e(dx)

    if dy < 0:
        walk_n(-dy)

    if dy > 0:
        walk_s(dy)

def walk_w(dx):
    # West is towards negative x
    global X
    # Check if this motion puts either western corer of our hitbox into the wall.
    # If so, move just next to the wall.
    if wall(floor(X-R-dx), floor(Y-R)) or (wall(floor(X-R-dx), floor(Y+R))):
        X = floor(X) + R
    else:
        X -= dx

def walk_e(dx):
    # Towards positive x
    global X
    if wall(floor(X+R+dx), floor(Y-R)) or (wall(floor(X+R+dx), floor(Y+R))):
        X = ceil(X) - R - 0.001 # We need to make sure The new X+R is rounded down or we get stuck.
    else:
        X += dx

def walk_n(dy):
    # Towards negative y
    global Y
    if wall(floor(X-R), floor(Y-R-dy)) or (wall(floor(X+R), floor(Y-R-dy))):
        Y = floor(Y) + R
    else:
        Y -= dy

def walk_s(dy):
    # Towards positive y
    global Y
    if wall(floor(X-R), floor(Y+R+dy)) or (wall(floor(X+R), floor(Y+R+dy))):
        Y = ceil(Y) - R - 0.001
    else:
        Y += dy


def ray(x, y, theta):
    # Find the first two intersections between the grid and a ray eminating
    # from the point (x, y) poiting in the direction theta, and also the
    # vector by which they points need to be incremented to trace the ray.
    #
    # The first point is on the gridlines in x direction.
    # The second pint in on the gridlines in y direction.
    #
    # Returns x1, y1, x2, y2, dx1, dy1, dx2, dy2
    # which is sufficient to trace a ray infinitely.

    # Wrap angles to [0, 2*pi]
    theta %= (2*pi)

    m = floor(x)
    n = floor(y)
    M = m + 1
    N = n + 1
    # If the ray is pointing close to the axes, the trigonometry
    # breaks down because either tan(theta) explodes, or 1/tan(theta) does.
    # This means that we have 8 cases to deal with: 4 quadrants, and 4
    # "along the axes".
    if -epsilon <= theta <= epsilon or 2*pi-epsilon <=theta <= 2*pi+epsilon:
        # Ray is pointing along the positive x-axis. Easy case. :D
        # We cover both ends of the interval to hedge against floating point
        # math leaving the angle in a weird spot where it doesnt trigger a
        # ray, and is also not wrapped around.
        return M, y, M+1,y, 1, 0, 1, 0

    if epsilon < theta < pi/2-epsilon:
        # Intersections are in the first quadrant.
        # We know there is an intersection at x = M,
        # and also one at y = N. Use trigonometry to
        # solve for the second coordinate. Note that
        # this breaks down when tan(theta) explodes.
        dx = M - x
        A = tan(theta)
        Dy = dx * A

        x1 = M
        y1 = y + Dy
        dx1 = 1
        dy1 = A

        dy = N - y
        B = 1 / tan(theta)
        Dx = dy * B

        x2 = x + Dx
        y2 = N
        dx2 = B
        dy2 = 1

        return x1, y1, x2, y2, dx1, dy1, dx2, dy2

    if pi/2-epsilon <= theta <= pi/2+epsilon:
        # Ray is pointing towards positive y.
        return x, N, x, N+1, 0, 1, 0, 1
    
    if pi/2+epsilon < theta < pi-epsilon:
        # Ray is in 2nd quadrant.
        psi = theta - pi/2 # This substition makes it prettier

        dx = x - m
        A =  1/tan(psi)
        Dy = dx * A

        x1 = m
        y1 = y + Dy
        dx1 = -1
        dy1 = A

        dy = N - y
        B = -tan(psi)
        Dx = dy * B

        x2 = x + Dx
        y2 = N
        dx2 = B
        dy2 = 1

        return x1, y1, x2, y2, dx1, dy1, dx2, dy2

    if pi-epsilon <= theta <= pi+epsilon:
        # Ray is pointing in the negative x direction.
        return m, y, m-1, y, -1, 0, -1, 0

    if pi+epsilon < theta < 3*pi/2-epsilon:
        # Ray is in the 3rd quadrant.
        psi = theta - pi

        dx = x - m
        A = -tan(psi)
        Dy = dx * A

        x1 = m
        y1 = y + Dy
        dx1 = -1
        dy1 = A

        dy = y - n
        B = -1/tan(psi)
        Dx = dy * B

        x2 = x + Dx
        y2 = n
        dx2 = B
        dy2 = -1

        return x1, y1, x2, y2, dx1, dy1, dx2, dy2

    if 3*pi/2-epsilon <= theta <= 3*pi/2+epsilon:
        # Ray is pointing in the negative y direction.
        return x, n, x, n-1, 0, -1, 0, -1

    if 3*pi/2+epsilon < theta < 2*pi-epsilon:
        # Ray is in the 4th quadrant
        psi = theta - 3*pi/2

        dx = M - x
        A = -1/tan(psi)
        Dy = dx * A

        x1 = M
        y1 = y + Dy
        dx1 = 1
        dy1 = A

        dy = y - n
        B = tan(psi)
        Dx = dy * B

        x2 = x + Dx
        y2 = n
        dx2 = B
        dy2 = -1

        return x1, y1, x2, y2, dx1, dy1, dx2, dy2

def dsq(x1, y1, x2, y2):
    # Returns the squared euclidian distance
    #   d([x1, y1], [x2, y2])^2
    return (x2 - x1)**2 + (y2 - y1)**2

def trace(x, y, x1, y1, x2, y2, dx1, dy1, dx2, dy2):
    # Follows the ray defined by the arguments until
    # a wall is reached. x, y is the coordinates of
    # the source, the rest is returned by ray(x, y, phi)
    # where x and y is also coords of the source.
    #
    # Returns wx, wy, ix, iy, tx
    #   x, y coordinate of the wall
    #   x, y coordinate of the intersection

    while True:
        while dsq(x, y, x1, y1) <= dsq(x, y, x2, y2):
            tx = floor(x1+epsilon*dx1)
            ty = floor(y1+epsilon*dy1)
            # If this tile is a wall, return
            if wall(tx, ty):
                return tx, ty, x1, y1
            # Keep looking... 
            x1 += dx1
            y1 += dy1
        
        # Now (x2, y2) is closer...
        while dsq(x, y, x2, y2) <= dsq(x, y, x1, y1):
            tx = floor(x2+epsilon*dx2)
            ty = floor(y2+epsilon*dy2)
            # If this tile is a wall, return
            if wall(tx, ty):
                return tx, ty, x2, y2
            # Keep looking... 
            x2 += dx2
            y2 += dy2

def texture_coordinates(ix, iy, vh, vy, th, tw):
    # Normalize to [0, 1]
    x = ix - floor(ix)
    y = iy - floor(iy)

    # Figure out which side of the wall we hit!
    if (y < x < (1 - y)) or (y > x > (1 - y)):
        tx = floor(x * tw)
    else:
        tx = floor(y * tw)

    # Figure out how low on the wall we hit
    ty = floor((vy/vh) * th)

    return tx, ty


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, caption="Raytracing Demo")
        pyxel.image(0).load(0, 0, "wall.png")

        pyxel.run(self.update, self.draw)

    def update(self):
        global phi
        
        # How much we increment epsilon every loop iteration
        # a key is pressed to turn around
        dphi = 7*epsilon

        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btn(pyxel.KEY_Z):
            phi = phi - dphi
        if pyxel.btn(pyxel.KEY_C):
            phi = phi + dphi

        # At each key press, check if moving this direction will move
        # EITHER ONE of two corners facing the wall INTO the wall. If
        # that is the case, clamp the delta so that we instead end up
        # right next to the wall.

        # Walking speed
        delta = 1/8

        if pyxel.btn(pyxel.KEY_W):
            dx = cos(phi)
            dy = sin(phi)
            walk(delta*dx, delta*dy)
        if pyxel.btn(pyxel.KEY_A):
            dx = sin(phi)
            dy = -cos(phi)
            walk(delta*dx, delta*dy)
        if pyxel.btn(pyxel.KEY_S):
            dx = -cos(phi)
            dy = -sin(phi)
            walk(delta*dx, delta*dy)
        if pyxel.btn(pyxel.KEY_D):
            dx = -sin(phi)
            dy = cos(phi)
            walk(delta*dx, delta*dy)


    def draw_minimap(self):
        # Draw the map
        for y in range(len(level)):
            for x in range(len(level[0])):
                tile = level[y][x]
                pyxel.rect(x*scale, y*scale, scale, scale, tile)

        # Find intersections for the middle ray.
        # x1, y1, x2, y2, dx1, dy1, dx2, dy2 = ray(X, Y, phi)

        wx, wy, ix, iy = trace(X, Y, *ray(X, Y, phi))
        pyxel.rectb(wx*scale, wy*scale, scale, scale, 8)

        # Draw facing ray
        pyxel.line(X*scale, Y*scale, ix*scale, iy*scale, 8)

        # Draw edges of FOV
        if draw_FOV:
            wx, wy, ix, iy = trace(X, Y, *ray(X, Y, left_extreme(phi)))
            pyxel.line(X*scale, Y*scale, ix*scale, iy*scale, 5)

            wx, wy, ix, iy = trace(X, Y, *ray(X, Y, left_extreme(phi) + FOV_rad))
            pyxel.line(X*scale, Y*scale, ix*scale, iy*scale, 11)


        # Draw player
        pyxel.rect(round((X-R)*scale), round((Y-R)*scale), 2*R*scale, 2*R*scale, 8)

    def draw_first_person(self):
        # Draw ceiling
        pyxel.rect(0, 0, WIDTH, horizon, 10)

        # Draw floor
        pyxel.rect(0, horizon, WIDTH, HEIGHT - horizon, 9)

        # Draw walls...

        # Calculate the angle of the LEFT MOST ray in the FOV.
        alpha = left_extreme(phi)

        for vx in range(WIDTH):
            ray_alpha = ray(X, Y, alpha);

            wx, wy, ix, iy = trace(X, Y, *ray_alpha)

            d = sqrt(dsq(X, Y, ix, iy))
            p = d * cos(alpha - phi)
            h = 2*HEIGHT/p

            top = horizon-floor(h/2)
            bot = horizon+floor(h/2)
            for vy in range(top, bot):
                # draw pixel at (vx, vy)
                tx, ty = texture_coordinates(ix, iy, h, vy -  top, 16, 16)
                # color = bricks[ty][tx]
                color = pyxel.image(0).get(tx, ty)

                pyxel.pset(vx, vy, color)

            alpha += epsilon


    def draw(self):
        pyxel.cls(0)
        self.draw_first_person();
        self.draw_minimap();


App()
