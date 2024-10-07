<!--完全无过滤靶场，只需逃逸即可-->
<?php 
// 开始计时
$start_time = microtime(true);

if (isset($_GET['ip'])) {
    $ip = $_GET['ip'];

    // 将 ping 命令的错误输出重定向到标准输出
    $command = "ping -c 1 " . $ip . " 2>&1";

    // 执行 ping 命令并捕获输出（包括错误信息）
    $a = shell_exec($command);

    // 输出结果（包括错误信息）
    echo "<pre>";
    print_r($a);
    echo "</pre>";
    
} else {
    die("no input");
}

// 检测目标文件是否被创建
if (file_exists('target.txt')) {
    echo "File 'target.txt' has been created!";
}

// 获取结束时间
$end_time = microtime(true);

// 计算执行时间
$execution_time = $end_time - $start_time;

// 以 'execution time: X.XX seconds' 格式输出执行时间
echo "<br>execution time: " . number_format($execution_time, 2) . " seconds";

?>

