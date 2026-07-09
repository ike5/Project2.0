/** Design Twitter.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-design-twitter/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private int time = 0;
        private final Map<Integer, List<int[]>> tweets = new HashMap<>();
        private final Map<Integer, Set<Integer>> follows = new HashMap<>();
        public void postTweet(int userId, int tweetId) {
            tweets.computeIfAbsent(userId, k -> new ArrayList<>()).add(new int[]{time++, tweetId});
        }
        public List<Integer> getNewsFeed(int userId) {
            Set<Integer> users = new HashSet<>(follows.getOrDefault(userId, Set.of()));
            users.add(userId);
            PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> Integer.compare(b[0], a[0]));
            // heap entry: [time, userId, index]
            for (int u : users) {
                List<int[]> ts = tweets.get(u);
                if (ts != null && !ts.isEmpty()) {
                    int i = ts.size() - 1;
                    heap.offer(new int[]{ts.get(i)[0], u, i});
                }
            }
            List<Integer> out = new ArrayList<>();
            while (!heap.isEmpty() && out.size() < 10) {
                int[] top = heap.poll();
                out.add(tweets.get(top[1]).get(top[2])[1]);
                if (top[2] > 0) {
                    int i = top[2] - 1;
                    heap.offer(new int[]{tweets.get(top[1]).get(i)[0], top[1], i});
                }
            }
            return out;
        }
        public void follow(int followerId, int followeeId) {
            follows.computeIfAbsent(followerId, k -> new HashSet<>()).add(followeeId);
        }
        public void unfollow(int followerId, int followeeId) {
            Set<Integer> s = follows.get(followerId);
            if (s != null) s.remove(followeeId);
        }

    public static void main(String[] args) {
        System.out.println("Twitter ready");
    }
}
