package models

import (
	"database/sql"
	"encoding/json"
	"log"
	"strings"
	"time"
)

// Task type constants
const (
	TaskTypeDevelop = "develop"
	TaskTypeAsk     = "ask"
	TaskTypeExport  = "export"
	TaskTypeExtend  = "extend"
	TaskTypeInit    = "init"

	AutoDevModuleCC    = "cc"
	AutoDevModuleCodex = "codex"
)

// AutoDevTask represents an autodev execution task
type AutoDevTask struct {
	ID          string     `json:"id"`
	Type        string     `json:"type"` // develop, ask, export
	Description string     `json:"description"`
	Options     string     `json:"options"` // JSON: {publish,build,push,module}
	Module      string     `json:"module"`
	Status      string     `json:"status"` // pending, running, completed, failed
	ExitCode    int        `json:"exit_code"`
	WorkDir     string     `json:"work_dir"`
	PID         int        `json:"pid"`
	CreatedAt   time.Time  `json:"created_at"`
	StartedAt   *time.Time `json:"started_at,omitempty"`
	CompletedAt *time.Time `json:"completed_at,omitempty"`
	ResultFile  string     `json:"result_file,omitempty"` // For ask: qa.md path
}

// AutoDevOptions task execution options
type AutoDevOptions struct {
	Publish bool   `json:"publish"`
	Build   bool   `json:"build"`
	Push    bool   `json:"push"`
	Module  string `json:"module"`
}

// NormalizeAutoDevModule converts user input to a supported execution module.
// Empty or unknown values always fall back to Claude Code for backward compatibility.
func NormalizeAutoDevModule(module string) string {
	switch strings.ToLower(strings.TrimSpace(module)) {
	case AutoDevModuleCodex:
		return AutoDevModuleCodex
	default:
		return AutoDevModuleCC
	}
}

// ParseAutoDevOptions decodes task options and applies backward-compatible defaults.
func ParseAutoDevOptions(raw string) AutoDevOptions {
	opts := AutoDevOptions{Module: AutoDevModuleCC}
	if strings.TrimSpace(raw) == "" {
		return opts
	}
	if err := json.Unmarshal([]byte(raw), &opts); err != nil {
		return AutoDevOptions{Module: AutoDevModuleCC}
	}
	opts.Module = NormalizeAutoDevModule(opts.Module)
	return opts
}

// InitAutoDevTasks initializes the autodev_tasks table
func (db *DB) InitAutoDevTasks() error {
	_, err := db.conn.Exec(`
		CREATE TABLE IF NOT EXISTS autodev_tasks (
			id TEXT PRIMARY KEY,
			type TEXT DEFAULT 'develop',
			description TEXT NOT NULL,
			options TEXT DEFAULT '{}',
			status TEXT DEFAULT 'pending',
			exit_code INTEGER DEFAULT 0,
			work_dir TEXT,
			pid INTEGER DEFAULT 0,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			started_at DATETIME,
			completed_at DATETIME,
			result_file TEXT
		);
		CREATE INDEX IF NOT EXISTS idx_autodev_tasks_status ON autodev_tasks(status);
		CREATE INDEX IF NOT EXISTS idx_autodev_tasks_created_at ON autodev_tasks(created_at);
	`)
	if err != nil {
		return err
	}
	// Run migration to ensure all columns exist
	return db.migrateAutoDevTasksTable()
}

// migrateAutoDevTasksTable ensures all required columns exist in the table
func (db *DB) migrateAutoDevTasksTable() error {
	// List of columns that should exist in the table
	requiredColumns := []struct {
		name string
		expr string
	}{
		{"type", "ALTER TABLE autodev_tasks ADD COLUMN type TEXT DEFAULT 'develop'"},
		{"description", "ALTER TABLE autodev_tasks ADD COLUMN description TEXT"},
		{"options", "ALTER TABLE autodev_tasks ADD COLUMN options TEXT DEFAULT '{}'"},
		{"status", "ALTER TABLE autodev_tasks ADD COLUMN status TEXT DEFAULT 'pending'"},
		{"exit_code", "ALTER TABLE autodev_tasks ADD COLUMN exit_code INTEGER DEFAULT 0"},
		{"work_dir", "ALTER TABLE autodev_tasks ADD COLUMN work_dir TEXT"},
		{"pid", "ALTER TABLE autodev_tasks ADD COLUMN pid INTEGER DEFAULT 0"},
		{"created_at", "ALTER TABLE autodev_tasks ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"},
		{"started_at", "ALTER TABLE autodev_tasks ADD COLUMN started_at DATETIME"},
		{"completed_at", "ALTER TABLE autodev_tasks ADD COLUMN completed_at DATETIME"},
		{"result_file", "ALTER TABLE autodev_tasks ADD COLUMN result_file TEXT"},
	}

	// Get existing columns
	rows, err := db.conn.Query("PRAGMA table_info(autodev_tasks)")
	if err != nil {
		return err
	}
	defer rows.Close()

	existingColumns := make(map[string]bool)
	for rows.Next() {
		var cid int
		var name, colType string
		var notnull, dfltValue, pk int
		if err := rows.Scan(&cid, &name, &colType, &notnull, &dfltValue, &pk); err != nil {
			continue
		}
		existingColumns[name] = true
	}

	// Add missing columns
	for _, col := range requiredColumns {
		if !existingColumns[col.name] {
			_, err := db.conn.Exec(col.expr)
			if err != nil {
				// Log but don't fail - column might already exist in some SQLite versions
				log.Printf("[AutoDev] Migration: attempted to add column %s, error: %v", col.name, err)
			}
		}
	}

	return nil
}

// CreateAutoDevTask creates a new task record
func (db *DB) CreateAutoDevTask(taskType, description, options, workDir string) (*AutoDevTask, error) {
	id := generateID(8)
	if taskType == "" {
		taskType = TaskTypeDevelop
	}
	_, err := db.conn.Exec(
		`INSERT INTO autodev_tasks (id, "type", description, options, work_dir, status) VALUES (?, ?, ?, ?, ?, 'pending')`,
		id, taskType, description, options, workDir,
	)
	if err != nil {
		return nil, err
	}
	return db.GetAutoDevTask(id)
}

// GetAutoDevTask retrieves a task by ID
func (db *DB) GetAutoDevTask(id string) (*AutoDevTask, error) {
	var task AutoDevTask
	var startedAt, completedAt sql.NullTime
	var resultFile sql.NullString
	err := db.conn.QueryRow(
		`SELECT id, "type", description, options, status, exit_code, work_dir, pid, created_at, started_at, completed_at, result_file
		 FROM autodev_tasks WHERE id = ?`, id,
	).Scan(
		&task.ID, &task.Type, &task.Description, &task.Options, &task.Status,
		&task.ExitCode, &task.WorkDir, &task.PID, &task.CreatedAt,
		&startedAt, &completedAt, &resultFile,
	)
	if err != nil {
		return nil, err
	}
	if task.Type == "" {
		task.Type = TaskTypeDevelop
	}
	if startedAt.Valid {
		task.StartedAt = &startedAt.Time
	}
	if completedAt.Valid {
		task.CompletedAt = &completedAt.Time
	}
	if resultFile.Valid {
		task.ResultFile = resultFile.String
	}
	task.Module = ParseAutoDevOptions(task.Options).Module
	return &task, nil
}

// CountAutoDevTasks returns total task count, optionally filtered by status/type.
// Empty string means "no filter".
func (db *DB) CountAutoDevTasks(status, taskType string) (int, error) {
	query := `SELECT COUNT(*) FROM autodev_tasks WHERE 1=1`
	var args []any
	if status != "" {
		query += ` AND status = ?`
		args = append(args, status)
	}
	if taskType != "" {
		query += ` AND "type" = ?`
		args = append(args, taskType)
	}
	var count int
	err := db.conn.QueryRow(query, args...).Scan(&count)
	return count, err
}

// ListAutoDevTasks lists tasks ordered by creation time desc with optional pagination/filter.
// limit=0 means no limit (returns all).
func (db *DB) ListAutoDevTasks(limit, offset int, status, taskType string) ([]*AutoDevTask, error) {
	query := `SELECT id, "type", description, options, status, exit_code, work_dir, pid, created_at, started_at, completed_at, result_file
		 FROM autodev_tasks WHERE 1=1`
	var args []any
	if status != "" {
		query += ` AND status = ?`
		args = append(args, status)
	}
	if taskType != "" {
		query += ` AND "type" = ?`
		args = append(args, taskType)
	}
	query += ` ORDER BY created_at DESC`
	if limit > 0 {
		query += ` LIMIT ? OFFSET ?`
		args = append(args, limit, offset)
	}
	rows, err := db.conn.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []*AutoDevTask
	for rows.Next() {
		var task AutoDevTask
		var startedAt, completedAt sql.NullTime
		var resultFile sql.NullString
		if err := rows.Scan(
			&task.ID, &task.Type, &task.Description, &task.Options, &task.Status,
			&task.ExitCode, &task.WorkDir, &task.PID, &task.CreatedAt,
			&startedAt, &completedAt, &resultFile,
		); err != nil {
			continue
		}
		if task.Type == "" {
			task.Type = TaskTypeDevelop
		}
		if startedAt.Valid {
			task.StartedAt = &startedAt.Time
		}
		if completedAt.Valid {
			task.CompletedAt = &completedAt.Time
		}
		if resultFile.Valid {
			task.ResultFile = resultFile.String
		}
		task.Module = ParseAutoDevOptions(task.Options).Module
		tasks = append(tasks, &task)
	}
	return tasks, nil
}

// ListAutoDevProjects returns unique work directories from all tasks
func (db *DB) ListAutoDevProjects() ([]string, error) {
	rows, err := db.conn.Query(
		`SELECT DISTINCT work_dir FROM autodev_tasks WHERE work_dir IS NOT NULL AND work_dir != '' ORDER BY work_dir`,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var projects []string
	for rows.Next() {
		var workDir string
		if err := rows.Scan(&workDir); err != nil {
			continue
		}
		projects = append(projects, workDir)
	}
	return projects, nil
}

// UpdateAutoDevTaskStatus updates task status and related fields
func (db *DB) UpdateAutoDevTaskStatus(id, status string, exitCode, pid int) error {
	now := time.Now()
	switch status {
	case "running":
		_, err := db.conn.Exec(
			`UPDATE autodev_tasks SET status = ?, pid = ?, started_at = ? WHERE id = ?`,
			status, pid, now, id,
		)
		return err
	case "completed", "failed":
		_, err := db.conn.Exec(
			`UPDATE autodev_tasks SET status = ?, exit_code = ?, completed_at = ? WHERE id = ?`,
			status, exitCode, now, id,
		)
		return err
	default:
		_, err := db.conn.Exec(
			`UPDATE autodev_tasks SET status = ? WHERE id = ?`,
			status, id,
		)
		return err
	}
}

// DeleteAutoDevTask deletes a task record
func (db *DB) DeleteAutoDevTask(id string) error {
	_, err := db.conn.Exec(`DELETE FROM autodev_tasks WHERE id = ?`, id)
	return err
}

// UpdateAutoDevTaskResult updates the result file path for ask tasks
func (db *DB) UpdateAutoDevTaskResult(id, resultFile string) error {
	_, err := db.conn.Exec(`UPDATE autodev_tasks SET result_file = ? WHERE id = ?`, resultFile, id)
	return err
}

// MarshalAutoDevOptions encodes options to JSON
func MarshalAutoDevOptions(opts AutoDevOptions) string {
	opts.Module = NormalizeAutoDevModule(opts.Module)
	b, _ := json.Marshal(opts)
	return string(b)
}

// Capabilities represents the system capabilities exposed via GET /api/autodev/capabilities
type Capabilities struct {
	System       string                   `json:"system"`
	Version      string                   `json:"version"`
	TaskTypes    []string                 `json:"task_types"`
	Capabilities map[string]CapabilitySet `json:"capabilities"`
	Boundaries   Boundaries               `json:"boundaries"`
}

// CapabilitySet represents a group of related capabilities
type CapabilitySet struct {
	Label       string   `json:"label"`
	Description string   `json:"description"`
	Items       []string `json:"items"`
}

// Boundaries defines what the system cannot do or requires
type Boundaries struct {
	Cannot   []string `json:"cannot"`
	Requires []string `json:"requires"`
}

// GetCapabilities returns the static capability清单 for clawweb/AutoDev
func GetCapabilities() *Capabilities {
	return &Capabilities{
		System:  "clawweb / AutoDev Web UI",
		Version: "1.0.0",
		TaskTypes: []string{
			"develop",
			"ask",
			"extend",
			"export",
			"init",
		},
		Capabilities: map[string]CapabilitySet{
			"task_management": {
				Label:       "任务管理与执行",
				Description: "提交和管理 AI Code Agent 任务",
				Items: []string{
					"develop - 全新项目开发",
					"ask - 基于项目上下文问答",
					"extend - 扩展已有项目",
					"export - 导出任务产物",
					"init - 初始化新项目",
				},
			},
			"code_understanding": {
				Label:       "代码理解与分析",
				Description: "对给定代码库进行结构化分析",
				Items: []string{
					"扫描项目结构",
					"分析代码架构",
					"理解模块依赖",
				},
			},
			"investigation": {
				Label:       "外部知识调研",
				Description: "通过搜索引擎获取外部参考信息",
				Items: []string{
					"WebSearch 搜索",
					"最佳实践查找",
					"技术方案调研",
				},
			},
			"file_exploration": {
				Label:       "文件与日志查看",
				Description: "监控任务执行过程和结果",
				Items: []string{
					"实时日志读取",
					"文件浏览",
					"产物下载",
				},
			},
			"system_admin": {
				Label:       "系统配置管理",
				Description: "管理工具链配置",
				Items: []string{
					"SSH Key 管理",
					"Claude/Clawtest 版本",
					"项目配置",
				},
			},
		},
		Boundaries: Boundaries{
			Cannot: []string{
				"DISCOVER 阶段禁止写实现代码",
				"禁止修改目标项目文件（需明确授权）",
				"禁止在需求不明确时自行决定实现方向",
			},
			Requires: []string{
				"具体任务描述或目标代码库路径",
				"如涉及基础设施（DB/Redis/MQ）需激活对应 Skill",
			},
		},
	}
}
