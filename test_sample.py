def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathHelper:
    def __init__(self, base):
        self.base = base
    
    def add(self, x):
        return self.base + x
    
    def multiply(self, x):
        return self.base * x 
