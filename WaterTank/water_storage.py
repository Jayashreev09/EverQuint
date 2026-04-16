"""Water Tank Problem brute force"""
def trapwater(block_heights):
    n = len(block_heights)
    units = 0
    for height in range(n):
        left_max = max(block_heights[:height+1])
        right_max = max(block_heights[height:]) 
        units += min(left_max, right_max) - block_heights[height]
    return units

block_height = [0, 4, 0, 0, 0, 6, 0, 6, 4, 0]
print(f"Input: {block_height}")
print(f"Output:     {trapwater(block_height)} Units")