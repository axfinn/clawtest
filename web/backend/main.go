package main

import (
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"clawweb/config"
	"clawweb/handlers"
	"clawweb/models"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func main() {
	// 加载配置文件
	configPath := os.Getenv("CONFIG_PATH")
	if configPath == "" {
		configPath = "./config.yaml"
	}
	cfg, err := config.Load(configPath)
	if err != nil {
		log.Printf("加载配置文件失败，使用默认配置: %v", err)
		cfg = config.Get()
	}

	// 配置端口：环境变量 > 配置文件 > 默认值
	port := os.Getenv("PORT")
	if port == "" {
		port = cfg.Server.Port
	}
	if port == "" {
		port = "7991"
	}

	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "./data/autodev.db"
	}

	// 确保数据目录存在
	os.MkdirAll("./data", 0755)

	// 初始化数据库
	db, err := models.NewDB(dbPath)
	if err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}
	defer db.Close()

	// 初始化 AutoDev Handler
	autoDevHandler := handlers.NewAutoDevHandler(db, cfg.AutoDev.AdminPassword, cfg.AutoDev.AutodevPath, cfg.AutoDev.DataDir, cfg.AutoDev.ClaudeHome)

	// 创建 Gin 引擎
	if cfg.Server.Mode == "release" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.Default()

	// CORS 配置
	r.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.Security.CORSOrigins,
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	// API 路由
	api := r.Group("/api")
	{
		autodev := api.Group("/autodev")
		{
			autodev.POST("/verify", autoDevHandler.VerifyPassword)
			autodev.GET("/capabilities", autoDevHandler.GetCapabilities)
			autodev.POST("/tasks", autoDevHandler.Submit)
			autodev.GET("/tasks", autoDevHandler.List)
			autodev.GET("/projects", autoDevHandler.ListProjects)
			autodev.GET("/tasks/:id", autoDevHandler.GetTask)
			autodev.GET("/tasks/:id/state", autoDevHandler.GetState)
			autodev.GET("/tasks/:id/files", autoDevHandler.GetFiles)
			autodev.GET("/tasks/:id/file", autoDevHandler.GetFile)
			autodev.GET("/tasks/:id/logs", autoDevHandler.GetLogs)
			autodev.GET("/tasks/:id/download", autoDevHandler.Download)
			autodev.GET("/tasks/:id/site/*filepath", autoDevHandler.GetSite)
			autodev.POST("/tasks/:id/stop", autoDevHandler.StopTask)
			autodev.DELETE("/tasks/:id", autoDevHandler.DeleteTask)

			autodev.POST("/ask", autoDevHandler.Ask)
			autodev.GET("/ask/:id", autoDevHandler.GetAskResult)

			autodev.POST("/extend", autoDevHandler.Extend)

			autodev.GET("/init/stream", autoDevHandler.InitProject)

			autodev.GET("/sshkey", autoDevHandler.GetSSHKey)
			autodev.POST("/sshkey/regenerate", autoDevHandler.RegenerateSSHKey)

			autodev.GET("/claude/version", autoDevHandler.GetClaudeVersion)
			autodev.GET("/claude/test", autoDevHandler.TestModel)
			autodev.GET("/claude/update/stream", autoDevHandler.UpdateClaude)

			autodev.GET("/clawtest/version", autoDevHandler.GetClawtestVersion)
			autodev.GET("/clawtest/update/stream", autoDevHandler.UpdateClawtest)
		}
	}

	// 获取静态文件目录的绝对路径
	staticDir, _ := filepath.Abs("./static")

	// 静态文件服务
	r.StaticFS("/static", http.Dir(staticDir))
	r.StaticFS("/assets", http.Dir(filepath.Join(staticDir, "assets")))

	// SPA 支持：所有未匹配的路由返回 index.html
	r.NoRoute(func(c *gin.Context) {
		// API 路径返回 404
		if strings.HasPrefix(c.Request.URL.Path, "/api") {
			c.Status(http.StatusNotFound)
			return
		}
		// 其他路径返回 index.html
		c.File("./static/index.html")
	})

	// 启动服务器
	addr := "0.0.0.0:" + port
	log.Printf("服务器启动在 %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}
