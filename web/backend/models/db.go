package models

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"os"
	"path/filepath"

	_ "github.com/mattn/go-sqlite3"
)

// DB 数据库连接
type DB struct {
	conn *sql.DB
}

// NewDB 创建数据库连接
func NewDB(dbPath string) (*DB, error) {
	// 确保目录存在
	os.MkdirAll(filepath.Dir(dbPath), 0755)

	conn, err := sql.Open("sqlite3", dbPath+"?_parse_time=true")
	if err != nil {
		return nil, err
	}

	db := &DB{conn: conn}
	if err := db.init(); err != nil {
		return nil, err
	}

	return db, nil
}

func (db *DB) init() error {
	// 初始化 autodev_tasks 表
	if err := db.InitAutoDevTasks(); err != nil {
		return err
	}
	return nil
}

// generateID 生成随机ID
func generateID(length int) string {
	bytes := make([]byte, length)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)[:length]
}

// Close 关闭数据库连接
func (db *DB) Close() error {
	return db.conn.Close()
}
