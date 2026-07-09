/** Hello, Java 21.
 *
 *  The simplest possible "Two Sum" to confirm the Java 21 toolchain works.
 *  Two Sum: given an array {@code nums} and a {@code target}, return the
 *  indices of the two numbers that add up to target. We assume exactly one
 *  solution exists.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out 00-setup/code/HelloNeetCode.java
 *      java -cp /tmp/out HelloNeetCode
 *
 *  We use the default package (no {@code package} statement) so the file
 *  can live anywhere without directory-prefix bookkeeping. Once you start
 *  writing real projects later, you would use a package statement whose
 *  directory mirrors the package name.
 */
import java.util.HashMap;
import java.util.Map;

public class HelloNeetCode {

    public static int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int need = target - nums[i];
            if (seen.containsKey(need)) {
                return new int[] { seen.get(need), i };
            }
            seen.put(nums[i], i);
        }
        return new int[] {};
    }

    public static void main(String[] args) {
        System.out.println("hello, java " + Runtime.version().feature());
        int[] a = twoSum(new int[] { 2, 7, 11, 15 }, 9);
        System.out.println("two_sum([2, 7, 11, 15], 9) -> [" + a[0] + ", " + a[1] + "]");
        int[] b = twoSum(new int[] { 3, 2, 4 }, 6);
        System.out.println("two_sum([3, 2, 4], 6)        -> [" + b[0] + ", " + b[1] + "]");
        int[] c = twoSum(new int[] { 3, 3 }, 6);
        System.out.println("two_sum([3, 3], 6)          -> [" + c[0] + ", " + c[1] + "]");
    }
}
