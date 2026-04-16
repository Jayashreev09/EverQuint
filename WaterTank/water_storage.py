"""Water Tank Problem brute force"""
'''
def water_storage(block_heights):
    n = len(block_heights)
    units = 0
    for height in range(n):
        left_max = max(block_heights[:height+1])
        right_max = max(block_heights[height:]) 
        units += min(left_max, right_max) - block_heights[height]
    return units
'''
"""Two pointer"""
def water_storage(block_heights):
    left, right = 0, len(block_heights) - 1
    left_max = right_max = units = 0
    while left < right:
        if block_heights[left] < block_heights[right]:
            left_max = max(left_max, block_heights[left])
            units += left_max - block_heights[left]
            left += 1
        else:
            right_max = max(right_max, block_heights[right])
            units += right_max - block_heights[right]
            right -= 1
    return units

block_height = [0, 4, 0, 0, 0, 6, 0, 6, 4, 0]
print(f"Input: {block_height}")
print(f"Output: {water_storage(block_height)} Units")