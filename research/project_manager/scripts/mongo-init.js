// MongoDB初始化脚本
// 用于AI科研助手的数据库初始化

print('开始初始化AI科研助手数据库...');

// 切换到ai_researcher数据库
db = db.getSiblingDB('ai_researcher');

// 创建管理员用户
db.createUser({
  user: 'admin',
  pwd: 'your_secure_password',
  roles: [
    { role: 'readWrite', db: 'ai_researcher' },
    { role: 'dbAdmin', db: 'ai_researcher' }
  ]
});

// 创建集合
db.createCollection('experiments');
db.createCollection('results');
db.createCollection('templates');
db.createCollection('knowledge_base');

// 创建索引
// 实验集合索引
db.experiments.createIndex({ "id": 1 }, { unique: true });
db.experiments.createIndex({ "status": 1 });
db.experiments.createIndex({ "created_at": -1 });
db.experiments.createIndex({ "objective": "text" });

// 结果集合索引
db.results.createIndex({ "experiment_id": 1 });
db.results.createIndex({ "created_at": -1 });

// 模板集合索引
db.templates.createIndex({ "name": 1 }, { unique: true });
db.templates.createIndex({ "type": 1 });

// 知识库集合索引
db.knowledge_base.createIndex({ "title": "text" });
db.knowledge_base.createIndex({ "tags": 1 });

print('AI科研助手数据库初始化完成！');

// 验证集合
print('当前数据库集合:');
db.getCollectionNames().forEach(function(collection) {
  print('  - ' + collection);
});

// 验证用户
print('当前数据库用户:');
db.getUsers().forEach(function(user) {
  print('  - ' + user.user);
});
