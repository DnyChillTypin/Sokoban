import sys
import traceback
import numpy as np

def test():
    try:
        from numba import njit

        @njit
        def _solve_matching_rec(costs_matrix, box_idx, mask, dp_cache, target_count):
            if box_idx == len(costs_matrix):
                return 0
            if dp_cache[box_idx, mask] != -1:
                return dp_cache[box_idx, mask]
            res = 999999
            for t_idx in range(target_count):
                if not (mask & (1 << t_idx)):
                    cost = costs_matrix[box_idx, t_idx]
                    m = cost + _solve_matching_rec(costs_matrix, box_idx + 1, mask | (1 << t_idx), dp_cache, target_count)
                    if m < res: 
                        res = m
            dp_cache[box_idx, mask] = res
            return res

        @njit
        def fast_solve_matching_wrapper(dist_matrix, boxes_array, target_count):
            num_boxes = len(boxes_array)
            costs = np.zeros((num_boxes, target_count), dtype=np.int32)
            for i in range(num_boxes):
                bx, by = boxes_array[i, 0], boxes_array[i, 1]
                for j in range(target_count):
                    costs[i, j] = dist_matrix[j, by, bx]
            dp_cache = np.full((num_boxes, 1 << target_count), -1, dtype=np.int32)
            return _solve_matching_rec(costs, 0, 0, dp_cache, target_count)

        # Mock data
        dist_matrix = np.zeros((2, 10, 10), dtype=np.int32)
        boxes_array = np.array([[1,1], [2,2]], dtype=np.int32)
        
        print("Compiling Numba function...")
        res = fast_solve_matching_wrapper(dist_matrix, boxes_array, 2)
        print("Success! Result:", res)

    except Exception as e:
        print("Exception occurred:")
        traceback.print_exc()

if __name__ == '__main__':
    test()
