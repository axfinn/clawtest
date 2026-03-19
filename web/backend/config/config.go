package config

import (
	"os"

	"gopkg.in/yaml.v3"
)

// Config 应用程序配置
type Config struct {
	Server    ServerConfig    `yaml:"server"`
	Security  SecurityConfig  `yaml:"security"`
	AutoDev   AutoDevConfig   `yaml:"autodev"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Port string `yaml:"port"` // 服务端口
	Mode string `yaml:"mode"` // 运行模式: debug, release
}

// SecurityConfig 安全配置
type SecurityConfig struct {
	CORSOrigins []string `yaml:"cors_origins"` // 允许的跨域来源
}

// AutoDevConfig AutoDev AI 任务配置
type AutoDevConfig struct {
	AdminPassword string `yaml:"admin_password"` // 访问密码（必填）
	AutodevPath   string `yaml:"autodev_path"`   // autodev 可执行文件路径，默认 /opt/autodev/autodev
	DataDir       string `yaml:"data_dir"`       // 任务工作目录，默认 ./data/autodev
	ClaudeHome    string `yaml:"claude_home"`    // 运行 Claude Code 时的 HOME 目录（可选）
	// 本地模式留空：自动使用 $HOME（skills 开箱即用）
	// Docker 模式：设为挂载路径，如 /home/autodev（需挂载 ~/.claude:/home/autodev/.claude）
	// 环境变量覆盖：CLAUDE_HOME
}

// 全局配置实例
var cfg *Config

// Get 获取全局配置
func Get() *Config {
	if cfg == nil {
		cfg = &Config{
			Server: ServerConfig{
				Port: "8080",
				Mode: "debug",
			},
			Security: SecurityConfig{
				CORSOrigins: []string{"*"},
			},
			AutoDev: AutoDevConfig{
				AutodevPath: "/opt/autodev/autodev",
				DataDir:     "./data/autodev",
			},
		}
	}
	return cfg
}

// Load 加载配置文件
func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	var config Config
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, err
	}

	// 应用默认值
	if config.Server.Port == "" {
		config.Server.Port = "8080"
	}
	if config.Server.Mode == "" {
		config.Server.Mode = "debug"
	}
	if len(config.Security.CORSOrigins) == 0 {
		config.Security.CORSOrigins = []string{"*"}
	}
	if config.AutoDev.AutodevPath == "" {
		config.AutoDev.AutodevPath = "/opt/autodev/autodev"
	}
	if config.AutoDev.DataDir == "" {
		config.AutoDev.DataDir = "./data/autodev"
	}

	// 支持环境变量覆盖
	if password := os.Getenv("AUTODEV_PASSWORD"); password != "" {
		config.AutoDev.AdminPassword = password
	}
	if autodevPath := os.Getenv("AUTODEV_PATH"); autodevPath != "" {
		config.AutoDev.AutodevPath = autodevPath
	}
	if dataDir := os.Getenv("AUTODEV_DATA_DIR"); dataDir != "" {
		config.AutoDev.DataDir = dataDir
	}
	if claudeHome := os.Getenv("CLAUDE_HOME"); claudeHome != "" {
		config.AutoDev.ClaudeHome = claudeHome
	}
	if port := os.Getenv("PORT"); port != "" {
		config.Server.Port = port
	}

	cfg = &config
	return &config, nil
}
