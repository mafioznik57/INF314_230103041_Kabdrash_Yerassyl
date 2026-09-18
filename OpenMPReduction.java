import java.util.concurrent.ThreadLocalRandom;

public class OpenMPReduction {

    static final long TOTAL_POINTS = 100_000_000L;
    static final int[] THREAD_COUNTS = {1, 2, 4, 8, 16, 32};

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Threads\tRuntime(ms)\tSpeedup\tEfficiency\tpi estimate");

        long baselineMs = 0;

        for (int t : THREAD_COUNTS) {
            Result r = runTrial(t);
            if (t == 1) baselineMs = r.elapsedMs;

            double speedup = (double) baselineMs / r.elapsedMs;
            double efficiency = (speedup / t) * 100.0;

            System.out.printf("%d\t%d\t%.2fx\t%.1f%%\t%.6f%n",
                    t, r.elapsedMs, speedup, efficiency, r.pi);
        }
    }

    static Result runTrial(int numThreads) throws InterruptedException {
        long pointsPerThread = TOTAL_POINTS / numThreads;
        Thread[] threads = new Thread[numThreads];
        final long[] localHits = new long[numThreads];

        long start = System.nanoTime();
        for (int t = 0; t < numThreads; t++) {
            final int idx = t;
            threads[t] = new Thread(() -> {
                long myHits = 0;
                for (long i = 0; i < pointsPerThread; i++) {
                    double x = ThreadLocalRandom.current().nextDouble();
                    double y = ThreadLocalRandom.current().nextDouble();
                    if (x * x + y * y <= 1.0) {
                        myHits++;
                    }
                }
                localHits[idx] = myHits; 
            });
            threads[t].start();
        }
        for (Thread th : threads) {
            th.join();
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        long totalHits = 0;
        for (long h : localHits) {
            totalHits += h;
        }
        double pi = 4.0 * totalHits / TOTAL_POINTS;

        return new Result(elapsedMs, pi);
    }

    static class Result {
        final long elapsedMs;
        final double pi;

        Result(long elapsedMs, double pi) {
            this.elapsedMs = elapsedMs;
            this.pi = pi;
        }
    }
}
