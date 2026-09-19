import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.atomic.AtomicLong;

public class SyncTrap {

    static final long TOTAL_POINTS = 50_000_000L;
    static final int NUM_THREADS = 4;

    public static void main(String[] args) throws InterruptedException {

        long startSingle = System.nanoTime();
        long hitsSingle = monteCarloSingleThreaded(TOTAL_POINTS);
        long elapsedSingleMs = (System.nanoTime() - startSingle) / 1_000_000;
        double piSingle = 4.0 * hitsSingle / TOTAL_POINTS;
        System.out.printf("Single-threaded:        pi ~= %.6f, time = %d ms%n",
                piSingle, elapsedSingleMs);

        AtomicLong totalHits = new AtomicLong(0);
        long pointsPerThread = TOTAL_POINTS / NUM_THREADS;
        Thread[] threads = new Thread[NUM_THREADS];

        long startMulti = System.nanoTime();
        for (int t = 0; t < NUM_THREADS; t++) {
            threads[t] = new Thread(() -> {
                for (long i = 0; i < pointsPerThread; i++) {
                    double x = ThreadLocalRandom.current().nextDouble();
                    double y = ThreadLocalRandom.current().nextDouble();
                    if (x * x + y * y <= 1.0) {
                        totalHits.incrementAndGet();
                    }
                }
            });
            threads[t].start();
        }
        for (Thread th : threads) {
            th.join();
        }
        long elapsedMultiMs = (System.nanoTime() - startMulti) / 1_000_000;
        double piMulti = 4.0 * totalHits.get() / TOTAL_POINTS;

        System.out.printf("4-thread (AtomicLong):  pi ~= %.6f, time = %d ms%n",
                piMulti, elapsedMultiMs);
        System.out.printf("Multi-threaded is %.2fx the single-threaded time (i.e. it got SLOWER)%n",
                (double) elapsedMultiMs / elapsedSingleMs);
    }

    static long monteCarloSingleThreaded(long points) {
        long hits = 0;
        for (long i = 0; i < points; i++) {
            double x = ThreadLocalRandom.current().nextDouble();
            double y = ThreadLocalRandom.current().nextDouble();
            if (x * x + y * y <= 1.0) hits++;
        }
        return hits;
    }
}
