# AI Agent Development Guidelines

This document outlines best practices for AI agents (like Claude) working on this cryptocurrency trading project. Following these guidelines ensures consistent development patterns, proper version control, and comprehensive knowledge capture. This file follows the [AGENTS.md](https://agents.md) format for agent-facing documentation.

## Git Commit Strategy

- **Rule**: Use [Conventional Commits](https://www.conventionalcommits.org/) for every commit. See [CONTRIBUTING.md](CONTRIBUTING.md) for types, format, and examples.
- **Commit after each major step**: After adding a feature, fixing a significant bug, completing a phase of work, or before switching to a different area. Don't wait for "perfect" code; atomic commits help.

## Knowledge Capture in LEARNINGS.md

### When to Update LEARNINGS.md
Update the learnings document whenever you discover or implement:

#### Technical Insights
- **API Quirks**: Unexpected behavior in Coinbase API
- **SDK Limitations**: Missing features or workarounds needed
- **Configuration Patterns**: Best practices for JSON structure
- **Error Handling**: Common errors and their solutions

#### Implementation Patterns
- **Code Architecture**: Successful design patterns used
- **Integration Methods**: How different components connect
- **Performance Optimizations**: Speed or efficiency improvements
- **Security Considerations**: Authentication or data protection insights

#### Troubleshooting Knowledge
- **Common Errors**: Error messages and their root causes
- **Debugging Techniques**: Methods that helped solve problems
- **Environment Issues**: Platform-specific solutions
- **Dependency Problems**: Package conflicts or version issues

### LEARNINGS.md Structure Guidelines

#### Categories to Maintain
1. **Technical Discoveries** - API behaviors, SDK quirks
2. **Implementation Patterns** - Successful code architectures
3. **Configuration Best Practices** - JSON structure recommendations
4. **Security Insights** - Authentication and credential management
5. **Performance Notes** - Optimization discoveries
6. **Troubleshooting Guide** - Error solutions and debugging tips

#### Update Format
```markdown
### New Category (if needed)
- **Discovery**: Brief description of what was learned
- **Context**: When/why this was discovered
- **Solution**: How it was addressed
- **Impact**: Why this matters for future development
```

## Development Workflow

### Recommended Process
1. **Plan**: Understand the task and create todos if complex
2. **Research**: Check existing code and documentation
3. **Implement**: Write code following existing patterns
4. **Test**: Verify functionality works correctly
5. **Document**: Update LEARNINGS.md if new insights discovered
6. **Commit**: Use conventional commit message (see [CONTRIBUTING.md](CONTRIBUTING.md))
7. **Validate**: Ensure system still works end-to-end

### Todo List Management
- Use TodoWrite tool for complex multi-step tasks
- Mark items as in_progress when starting work
- Complete todos immediately after finishing tasks
- Add new todos if additional work is discovered

## Code Quality Standards

### Follow Existing Patterns
- **Configuration**: Use JSON files for user-modifiable settings
- **Error Handling**: Consistent try/except blocks with user-friendly messages
- **Validation**: Comprehensive input validation before API calls
- **Logging**: Print statements for user feedback and debugging
- **Security**: Never commit credentials or sensitive data

### Integration Requirements
- **Backward Compatibility**: Don't break existing functionality
- **Configuration-Driven**: New features should be configurable
- **Validation**: Always validate inputs and configurations
- **Testing**: Include dry-run modes for safe testing

## Knowledge Preservation

### Document These Types of Insights
- **"This took longer than expected because..."**
- **"The API documentation didn't mention that..."**
- **"We had to implement a workaround for..."**
- **"The best practice turned out to be..."**
- **"Future developers should know that..."**

### Examples of Good Learning Entries
```markdown
### Price Precision Requirements
- **Discovery**: Each trading pair has specific decimal place requirements
- **Context**: INVALID_PRICE_PRECISION errors when placing orders
- **Solution**: Always check product.price_increment and round accordingly
- **Impact**: Critical for successful order placement

### ECDSA vs Ed25519 Keys
- **Discovery**: Advanced Trading API only supports ECDSA keys
- **Context**: Authentication failures with Ed25519 keys
- **Solution**: Generate ECDSA keys specifically for this API
- **Impact**: Must be documented clearly for setup instructions
```

## File Organization

### When to Create New Files
- **Utilities**: Separate validation, configuration, or helper functions
- **Examples**: Template files or demonstration scripts
- **Documentation**: Specific guides or reference materials
- **Tests**: Validation or testing scripts

### Naming Conventions
- **Scripts**: `action_noun.py` (e.g., `execute_trading_strategy.py`)
- **Utilities**: `noun_action.py` (e.g., `config_validator.py`)
- **Examples**: `example_noun.py` or `noun.example.json`
- **Documentation**: `NOUN.md` in all caps for important docs

## Version Control Best Practices

### What to Commit
- ✅ Source code and scripts
- ✅ Configuration templates (.example.json)
- ✅ Documentation updates
- ✅ Requirements and dependencies
- ❌ Personal configurations (trading_config.json)
- ❌ API credentials or keys
- ❌ Temporary test files

### Branching Strategy
- **Main Branch**: Stable, tested code only
- **Feature Branches**: For experimental or complex features
- **Commit Early**: Don't wait for perfect code
- **Atomic Commits**: Each commit should represent one logical change

## Handoff Considerations

### Information for Next AI Agent
- **Current State**: What's working and what's in progress
- **Recent Changes**: What was just implemented or modified
- **Known Issues**: Any problems or limitations discovered
- **Next Steps**: Logical progression for continued development

### Context Preservation
- Update LEARNINGS.md with recent discoveries
- Ensure configuration examples are current
- Document any temporary workarounds
- Note any testing or validation that was performed

---

*This document should be updated as development practices evolve and new insights are discovered.*
