import random

# Producers should produce lists of tuples where each tuple
# contains a list of lights to light containing tuples of a light
# nmber and color.


class Producer:
    def __init():
        pass

    def step(self):
        return [1, 2, 3]


class Popcorn(Producer):
    def __init__(self, size=300):
        super().__init__()
        self.color = Color(0, 0, 128)
        self.size = size

    def step(self):
        return random.sample(range(size), 10)

    def color(self):
        return self.color


class Fill(Producer):
    def __init__(self, direction=1, size=300):
        super().__init__()
        self.color = Color(0, 0, 128)
        self.size = size
        self.done = False
        self.light = 0

    def step(self):
        if self.done:
            return []
        light = self.light
        self.light += 1
        if self.light >= self.size:
            self.done = True
        return [light]

    def color(self):
        return self.color

class Animator:
    def __init__(self, producer):
        self.lit = []
        self.light_color = Color(0, 0, 255)
        self.producer = producer

    def restore_previous():
        for i, color in self.lit:
            strip[i] = color

    def light_current(self, light_list):
        """light the current lights"""
        self.lit = []

        # grab the producer's default color
        color = self.producer.color()

        # for all the lights the producer returned
        for thing in light_list:
            # if the element's a tuple it contains a light number
            # and a color else it's just a light number and
            # we use the producer's default color
            if thing is tuple:
                light, color = thing
            else:
                light = thing
            # copy the current color then set the new color
            self.lit.append((light, strip[light]))
            strip[light] = self.light_color

    def step(self):
        """step the animation"""
        self.clear_previous()
        light_list = self.producer.step()
        self.light_current(light_list)


#fill1 = Fill()
#a = Animator(fill1)
#a.step()
