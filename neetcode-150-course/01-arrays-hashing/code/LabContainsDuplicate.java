// Lab 01B — Contains Duplicate (reference solution).
//
// Run:
//     mkdir -p /tmp/out
//     javac -d /tmp/out 01-arrays-hashing/code/LabContainsDuplicate.java
//     java -ea -cp /tmp/out LabContainsDuplicate
import java.util.HashSet;
import java.util.Set;

public class LabContainsDuplicate {
    public static boolean containsDuplicate(int[] nums) {
        Set<Integer> seen = new HashSet<>();
        for (int x : nums) {
            if (!seen.add(x)) return true;
        }
        return false;
    }

    public static void main(String[] args) {
        assert containsDuplicate(new int[]{1, 2, 3, 1});
        assert !containsDuplicate(new int[]{1, 2, 3, 4});
        assert containsDuplicate(new int[]{1, 1, 1, 3, 3, 4, 3, 2, 4, 2});
        assert !containsDuplicate(new int[]{});
        System.out.println("all tests passed");
    }
}
