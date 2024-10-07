<!--过滤命令关键字靶场-->
<?php
// 启用错误显示
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// 开始计时
$start_time = microtime(true);

// 定义需要过滤的关键字列表
$filtered_keywords = [
    'id', 'sleep', 'ls', 'whoami', 'ifconfig', 'cat', 'touch', 'tac', 'nl', 'more', 'tail', 'pr'
];

// 检查 POST 请求中的 'command' 参数是否存在
if (isset($_GET['ip'])) {
    $command = $_GET['ip'];

    // 检查是否包含任何被过滤的关键字
    foreach ($filtered_keywords as $keyword) {
        if (stripos($command, $keyword) !== false) {
            // 如果找到被过滤的关键字，则显示失败消息
            echo "escape failed";
            exit;
        }
    }
    echo "input:".$command."\n";
    // 将命令中的错误输出重定向到标准输出
    $command_with_error = "ping -c 1 " . $command . " 2>&1";
    // 执行命令并捕获输出
    $output = shell_exec($command_with_error);

    // 显示命令输出（包括错误信息）
    echo "<pre>";
    echo $output;
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

// 显示执行时间
echo "<br>execution time: " . number_format($execution_time, 2) . " seconds";
?>

