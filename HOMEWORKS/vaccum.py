def square_vacuum(side):
    room_area = side * side
    coverage = room_area
    ineff = room_area - coverage
    print("\nSquare Vacuum")
    print("Room area:", room_area)
    print("Coverage:",coverage)
    print("Inefficiency:",ineff)
    print("Efficiency:",coverage / room_area * 100, "%")

def circle_vacuum(side):
    room_area = side * side
    r = side / 2
    coverage = 3.14 * r * r
    ineff = room_area - coverage
    print("\nCircle Vacuum")
    print("Room area:", room_area)
    print("Coverage:",coverage)
    print("Inefficiency:", ineff)
    print("Efficiency:",coverage / room_area * 100, "%")

def triangle_vacuum(side):
    room_area = side * side
    coverage = 1.732 / 4 * (side * side)
    ineff = room_area - coverage
    print("\nTriangle Vacuum")
    print("Room area:", room_area)
    print("Coverage:", coverage)
    print("Inefficiency:",ineff)
    print("Efficiency:",coverage / room_area * 100, "%")

print("Choose shape: 1.square  2.circle  3.triangle")
shape = int(input("Enter Number: "))

side = float(input("Enter room side length: "))

if shape == 1:
    square_vacuum(side)
elif shape == 2:
    circle_vacuum(side)
elif shape == 3:
    triangle_vacuum(side)
else:
    print("Invalid shape")
