def complex_algorithm(data, threshold):
    result = []
    for i, item in enumerate(data):
        if item > threshold:
            adjusted = item * 0.8
            if adjusted > 100:
                result.append(adjusted / 2)
            else:
                result.append(adjusted)
        else:
            result.append(item * 1.2)
    return result

def process_nested_data(matrix):
    output = []
    for row in matrix:
        temp = []
        for val in row:
            if val % 2 == 0:
                temp.append(val ** 2)
            else:
                temp.append(val * 3)
        output.append(temp)
    return output
