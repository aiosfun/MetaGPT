"""
Module containing functions for complex data processing algorithms.
"""

def complex_algorithm(data, threshold):
    """
    Applies a complex algorithm to each item in the input data based on a threshold.

    Args:
        data (list of float): The input data list containing numerical values.
        threshold (float): The threshold value used for conditional logic.

    Returns:
        list of float: A new list with processed values according to the algorithm.

    Raises:
        ValueError: If the input data is empty or not a list.
    """
    if not isinstance(data, list) or not data:
        raise ValueError("Input data must be a non-empty list.")
    
    result = []
    for i, item in enumerate(data):
        # Check if the current item exceeds the threshold
        if item > threshold:
            adjusted = item * 0.8  # Reduce the value by 20%
            # Further adjust if the reduced value is greater than 100
            if adjusted > 100:
                result.append(adjusted / 2)  # Halve the value
            else:
                result.append(adjusted)
        else:
            result.append(item * 1.2)  # Increase the value by 20%
    return result

def process_nested_data(matrix):
    """
    Processes a nested data structure (matrix) by applying specific operations to each element.

    Args:
        matrix (list of list of int): The input matrix containing numerical values.

    Returns:
        list of list of int: A new matrix with processed values according to the algorithm.

    Raises:
        ValueError: If the input matrix is empty or not a list of lists.
    """
    if not isinstance(matrix, list) or not all(isinstance(row, list) for row in matrix):
        raise ValueError("Input must be a non-empty list of lists.")
    
    output = []
    for row in matrix:
        temp = []
        for val in row:
            # Check if the current value is even
            if val % 2 == 0:
                temp.append(val ** 2)  # Square the value
            else:
                temp.append(val * 3)  # Triple the value
        output.append(temp)
    return output