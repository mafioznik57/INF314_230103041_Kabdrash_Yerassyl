import java.util.concurrent.ThreadLocalRandom;

public class PhantomBug {

    static long totalHits = 0;

    static final long TOTAL_POINTS = 50_000_000L;
    static final int NUM_THREADS = 4;

    public static void main(String[] args) throws InterruptedException {
        for (int run = 1; run <= 5; run++) {
            totalHits = 0; // reset between runs
            long pointsPerThread = TOTAL_POINTS / NUM_THREADS;

            Thread[] threads = new Thread[NUM_THREADS];
            long start = System.nanoTime();

            for (int t = 0; t < NUM_THREADS; t++) {
                threads[t] = new Thread(() -> {
                    for (long i = 0; i < pointsPerThread; i++) {
                        double x = ThreadLocalRandom.current().nextDouble();
                        double y = ThreadLocalRandom.current().nextDouble();
                        if (x * x + y * y <= 1.0) {
                            totalHits++; 
                        }
                    }
                });
                threads[t].start();
            }
            for (Thread th : threads) {
                th.join();
            }

            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            double pi = 4.0 * totalHits / TOTAL_POINTS;
            System.out.printf("Run %d: pi ~= %.6f  (hits=%d, time=%d ms)%n",
                    run, pi, totalHits, elapsedMs);
        }
    }
}
