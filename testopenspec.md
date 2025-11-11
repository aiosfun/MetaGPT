# OpenSpec Integration Testing Guide

This document provides comprehensive testing instructions for the OpenSpec integration enhancement in MetaGPT. Follow the steps below to validate that all OpenSpec components are working correctly.

## Prerequisites

1. Ensure you're on the `metagpt_openspec` branch:
   ```bash
   git checkout metagpt_openspec
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify OpenSpec modules can be imported:
   ```bash
   python -c "from metagpt.openspec import OpenSpecTemplateEngine, OpenSpecValidator; print('✅ OpenSpec modules imported')"
   ```

## Quick Start

Run the comprehensive test suite:
```bash
python testopenspec.py
```

## Test Coverage

The test suite covers the following areas:

### Phase 1: Core Framework Tests
- **Template Engine**: Jinja2 template rendering for requirements, designs, and tasks
- **Validation System**: Multi-level validation with error/warning/info feedback
- **Data Models**: Pydantic model validation and structure

### Phase 2: Action Tests
- **WritePRDWithOpenSpec**: OpenSpec-compliant requirement generation
- **WriteDesignWithOpenSpec**: Design generation with requirement traceability
- **WriteTasksWithOpenSpec**: Task generation following design specifications

### Phase 3: Role Enhancement Tests
- **ProductManager**: OpenSpec mode with automatic action selection
- **Architect**: OpenSpec mode with design generation enhancement
- **ProjectManager**: OpenSpec mode with task generation enhancement

### Phase 4: Advanced Tests
- **Traceability Manager**: Single-path requirement→design→task tracking
- **Review System**: Multi-stage review workflow and quality gates
- **End-to-End Workflow**: Complete MetaGPT workflow integration
- **Performance**: Multiple specification generation performance

## Expected Results

### Successful Test Indicators:

1. **All Imports Succeed**: No ImportError or module errors
2. **Templates Render**: Valid OpenSpec format output
3. **Validation Works**: Clear feedback on specification quality
4. **Actions Generate**: Structured specifications with proper formatting
5. **Roles Toggle**: set_openspec_mode() switches between modes correctly
6. **Traceability Maintains**: Complete requirement→design→task chain
7. **Performance Acceptable**: < 5 seconds per specification generation

### Performance Benchmarks:

- **Template Rendering**: < 1 second per specification
- **Validation**: < 0.5 seconds per specification
- **Action Generation**: < 3 seconds per specification
- **End-to-End Workflow**: < 10 seconds for simple requirements
- **Batch Processing**: < 2 seconds per specification in parallel

## Troubleshooting

### Common Issues and Solutions:

#### 1. Import Errors
```
ImportError: cannot import name 'OpenSpecTemplateEngine'
```
**Solution**: Ensure you're on the correct branch and all files are committed

#### 2. Template Rendering Errors
```
TemplateError: 'title' is undefined
```
**Solution**: Check template data structure and ensure all required fields are provided

#### 3. Validation Too Strict
```
ValidationError: All scenarios must have Given/When/Then format
```
**Solution**: Adjust validation strictness or fix scenario formatting

#### 4. Action Selection Issues
```
Role doesn't select OpenSpec action
```
**Solution**: Verify set_openspec_mode(True) is called and action import is successful

#### 5. Performance Issues
```
Generation takes > 10 seconds
```
**Solution**: Check for LLM API issues or optimize template caching

## Test Details

### Individual Test Files

The main `testopenspec.py` script contains all tests, but you can run specific components:

```bash
# Test just the template engine
python -c "
import asyncio
from testopenspec import test_template_engine
asyncio.run(test_template_engine())
"

# Test just validation
python -c "
from testopenspec import test_validation_system
test_validation_system()
"

# Test just the workflow
python -c "
import asyncio
from testopenspec import test_end_to_end_workflow
asyncio.run(test_end_to_end_workflow())
"
```

### Validation Output Format

Expected validation results:
```
Validation Results:
✅ Valid: True
Errors: 0
Warnings: 2
  - Consider adding more detailed acceptance criteria
  - Some scenarios could benefit from more specific Given conditions
```

### Traceability Reports

Expected traceability output:
```
Traceability Report (Requirement → Design → Task Chain)

## Requirements Coverage
### requirement_user_auth
**Requirement**: User Authentication System
**Design Coverage**: ✅ (2 design components)
**Tasks**: 5/5 completed
**Overall Coverage**: 100.0%

## Traceability Chain Gaps
### requirements_without_design_coverage: 0
### designs_without_task_coverage: 0

## Statistics
- **Total Requirements**: 1
- **Fully Covered Requirements**: 1/1
- **Total Design Components**: 2
- **Total Tasks**: 5
- **Completed Tasks**: 5
```

## Advanced Testing Options

### Custom Requirements Testing

You can test with your own requirements:

```python
# Add to testopenspec.py or run directly
import asyncio
from metagpt.actions.write_prd_openspec import WritePRDWithOpenSpec

async def test_custom():
    action = WritePRDWithOpenSpec()
    result = await action.run("Your custom requirement here")
    print(result)

asyncio.run(test_custom())
```

### Parallel Processing Testing

Test multiple specifications simultaneously:

```bash
python testopenspec.py --parallel
```

### Integration with Existing MetaGPT

Test the full SoftwareCompany workflow:

```python
from metagpt.software_company import SoftwareCompany

# Test with OpenSpec enabled
company = SoftwareCompany()
result = await company.run("Build a task management app")
```

## Next Steps

After running all tests successfully:

1. **Review Results**: Check all test outputs for any warnings or issues
2. **Performance Tuning**: Optimize based on performance metrics
3. **Documentation**: Update any documentation based on findings
4. **Production Ready**: Consider deployment if all tests pass

## Support

If you encounter any issues during testing:

1. Check the error messages carefully
2. Verify all dependencies are installed
3. Ensure you're on the correct branch
4. Run individual component tests to isolate issues
5. Check the MetaGPT logs for additional debugging information

Remember that the OpenSpec integration maintains full backward compatibility, so existing MetaGPT functionality should continue to work alongside the new OpenSpec features.