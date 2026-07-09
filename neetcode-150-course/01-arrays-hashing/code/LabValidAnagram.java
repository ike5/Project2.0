// Lab 01E — Valid Anagram (reference solution).
//
// Run:
//     mkdir -p /tmp/out
//     javac -d /tmp/out 01-arrays-hashing/code/LabValidAnagram.java
//     java -ea -cp /tmp/out LabValidAnagram
public class LabValidAnagram {
    public static boolean isAnagram(String s, String t) {
        if (s.length() != t.length()) return false;
        int[] count = new int[26];
        for (int i = 0; i < s.length(); i++) {
            count[s.charAt(i) - 'a']++;
            count[t.charAt(i) - 'a']--;
        }
        for (int c : count) if (c != 0) return false;
        return true;
    }

    public static void main(String[] args) {
        assert isAnagram("anagram", "nagaram");
        assert !isAnagram("rat", "car");
        assert isAnagram("a", "a");
        assert !isAnagram("ab", "a");
        assert isAnagram("", "");
        System.out.println("all tests passed");
    }
}
