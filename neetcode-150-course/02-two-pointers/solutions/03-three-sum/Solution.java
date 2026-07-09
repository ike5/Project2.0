/** 3Sum.
 *
 *  02 Two Pointers - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-three-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> threeSum(int[] nums) {
            Arrays.sort(nums);
            int n = nums.length;
            List<List<Integer>> out = new ArrayList<>();
            for (int i = 0; i < n - 2; i++) {
                if (i > 0 && nums[i] == nums[i - 1]) continue;
                int l = i + 1, r = n - 1;
                while (l < r) {
                    int s = nums[i] + nums[l] + nums[r];
                    if (s == 0) {
                        out.add(Arrays.asList(nums[i], nums[l], nums[r]));
                        while (l < r && nums[l] == nums[l + 1]) l++;
                        while (l < r && nums[r] == nums[r - 1]) r--;
                        l++;
                        r--;
                    } else if (s < 0) {
                        l++;
                    } else {
                        r--;
                    }
                }
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("threeSum ready");
    }
}
