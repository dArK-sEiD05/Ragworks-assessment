# Ragworks AI Interview System

A comprehensive technical interview platform designed to evaluate software engineering candidates across different specializations through practical, role-specific challenges.

## 🎯 System Overview

**IMPORTANT: Candidates should ONLY work in their target role directory. You do NOT need to complete all roles or understand the entire system.**

This platform provides:
- **Role-specific assessments** tailored to different engineering disciplines
- **Modular infrastructure** with only the services you need
- **Practical challenges** that mirror real-world development scenarios
- **Clear evaluation criteria** and submission guidelines

## 🚀 Choose Your Challenge

### 🏗️ **Backend Engineers** (`backend-engineer/`)
**Focus**: API development, database design, system architecture
- **Duration**: 2-3 coding problems (6-10 hours total)
- **Deliverables**: Working APIs, database schemas, system designs
- **Tech Stack**: FastAPI, PostgreSQL, Redis, Docker, message queues
- **Infrastructure**: `docker-compose/start-backend.sh`

### 🎨 **Frontend Engineers** (`frontend-engineer/`)
**Focus**: UI/UX implementation, modern web development
- **Duration**: 2-3 UI/UX challenges (6-10 hours total)
- **Deliverables**: Interactive components, responsive layouts, optimized applications
- **Tech Stack**: React, Next.js, TypeScript, Tailwind CSS, testing frameworks
- **Infrastructure**: `docker-compose/start-frontend.sh`

### 🧪 **QA Engineers** (`qa-engineer/`)
**Focus**: Test automation, quality assurance, testing strategies
- **Duration**: 2-3 testing challenges (6-10 hours total)
- **Deliverables**: Test frameworks, automation scripts, testing strategies
- **Tech Stack**: Python, Selenium/Playwright, Pytest, performance tools
- **Infrastructure**: `docker-compose/start-qa.sh`

### 🏗️ **DevOps Engineers** (`devops-engineer/`)
**Focus**: Infrastructure as Code, CI/CD, monitoring, security
- **Duration**: 2-3 infrastructure challenges (6-10 hours total)
- **Deliverables**: Terraform configs, CI/CD pipelines, monitoring dashboards
- **Tech Stack**: Terraform, Kubernetes, Docker, Prometheus, CI/CD tools
- **Infrastructure**: `docker-compose/start-devops.sh`

### 🤖 **LLM Challenge** (`llm-challenge/`) - *Optional*
**Focus**: LLM integration, RAG implementation, full-stack development
- **Duration**: Build a complete application (timeline flexible)
- **Deliverables**: Streamlit + FastAPI RAG application with authentication
- **Tech Stack**: Streamlit, FastAPI, LLM APIs, Vector databases
- **Senior Bonus**: Email integration for automatic responses

# Backend Engineer Assessment

I have successfully completed the backend part of the assessment.
- **Vector DBs**: Qdrant, Pinecone, Chroma, Weaviate
- **Tools**: Ollama, LM Studio, Hugging Face

## 📚 Documentation

- [Backend Engineer Assessment](./backend-engineer/README.md) - **Complete 2-3 problems in 6-10 hours**
- [Frontend Engineer Assessment](./frontend-engineer/README.md) - **Complete 2-3 problems in 6-10 hours**
- [QA Engineer Assessment](./qa-engineer/README.md) - **Complete 2-3 problems in 6-10 hours**
- [DevOps Engineer Assessment](./devops-engineer/README.md) - **Complete 2-3 problems in 6-10 hours**
- [LLM Challenge](./llm-challenge/README.md) - **Build Streamlit + FastAPI RAG application**
- [Docker Compose Services](./docker-compose/README.md) - **Role-specific infrastructure setup**

## 🚦 Management Commands

### **Start Services**
```bash
cd docker-compose
./start-[role].sh
```

### **Stop Services**
```bash
docker-compose -f base.yml -f [role].yml down
```

### **View Logs**
```bash
docker-compose -f base.yml -f [role].yml logs -f [service]
```

### **Check Status**
```bash
docker-compose -f base.yml -f [role].yml ps
```

## 💡 Best Practices & Success Tips

### **Development**
- **Start Simple**: Begin with a working solution, then optimize
- **Test Early**: Write tests as you develop, not after
- **Document**: Keep documentation updated with your code
- **Version Control**: Use meaningful commits and branches
- **Error Handling**: Implement proper error handling and validation

### **Infrastructure**
- **Use Role-Specific Scripts**: Start only the services you need
- **Check Service Health**: Ensure services are running before starting development
- **Monitor Resources**: Watch memory and CPU usage
- **Clean Up**: Stop services when not in use

### **Submission**
- **README Quality**: Clear setup instructions are crucial
- **Working Solution**: Ensure everything runs without manual intervention
- **Environment Setup**: Document all dependencies and configuration
- **Testing Instructions**: Include how to test your solution

## 🔍 Troubleshooting

### **Common Issues**
- **Port Conflicts**: Edit port mappings in docker-compose files
- **Memory Issues**: Adjust memory limits for resource-intensive services
- **Network Issues**: Ensure Docker network exists and services can communicate
- **Service Dependencies**: Start base services before role-specific ones

### **Getting Help**
- Check the role-specific README files
- Review the docker-compose documentation
- Check service logs: `docker-compose logs -f [service]`
- Verify service health: `docker-compose ps`
- Contact engineering@ragworks.ai for support

## 🤝 Support

For technical support or questions:
1. Check the role-specific documentation
2. Review the docker-compose guides
3. Contact the development team at engineering@ragworks.ai

---

**Good luck! We're excited to see what you build! 🚀**
