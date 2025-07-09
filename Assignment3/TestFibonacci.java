public class TestFibonacci {
    public static void main(String[] args) {
        System.out.println("开始 Fibonacci 性能测试...");
        
        long startTime = System.currentTimeMillis();
        long totalCalculations = 0;
        
        // 运行30秒的计算密集任务
        while (System.currentTimeMillis() - startTime < 90000) {
            // 添加一些其他类型的计算
            performMatrixMultiplication();
            performStringOperations();
            // 计算不同大小的 Fibonacci 数列
            for (int i = 20; i <= 30; i++) {
                long result = fibonacci(i);
                totalCalculations++;
            }
        }
        
        long endTime = System.currentTimeMillis();
        System.out.println("测试完成！");
        System.out.println("总运行时间: " + (endTime - startTime) + " 毫秒");
        System.out.println("总计算次数: " + totalCalculations);
        System.out.println("平均每秒计算: " + (totalCalculations * 1000 / (endTime - startTime)));
    }
    
    // 递归计算 Fibonacci 数列 (CPU 密集型)
    static long fibonacci(int n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
    
    // 矩阵乘法计算 (内存密集型)
    static void performMatrixMultiplication() {
        int size = 100;
        int[][] a = new int[size][size];
        int[][] b = new int[size][size];
        int[][] c = new int[size][size];
        
        // 初始化矩阵
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                a[i][j] = i + j;
                b[i][j] = i * j;
            }
        }
        
        // 矩阵乘法
        for (int i = 0; i < size; i++) {
            for (int j = 0; j < size; j++) {
                for (int k = 0; k < size; k++) {
                    c[i][j] += a[i][k] * b[k][j];
                }
            }
        }
    }
    
    // 字符串操作 (垃圾回收密集型)
    static void performStringOperations() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 1000; i++) {
            sb.append("Test string ").append(i).append(" ");
        }
        
        String result = sb.toString();
        String[] parts = result.split(" ");
        
        // 创建一些临时对象
        for (int i = 0; i < 100; i++) {
            String temp = "Temporary string " + i;
            temp = temp.toUpperCase().toLowerCase();
        }
    }
}
