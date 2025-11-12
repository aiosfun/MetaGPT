#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

from metagpt.roles.code_annotator import CodeAnnotator
from metagpt.logs import logger


async def main():
    if len(sys.argv) < 2:
        print("Usage: python annotate_code.py <file_or_directory_path>")
        print("\nExamples:")
        print("  python annotate_code.py test_sample.py")
        print("  python annotate_code.py src/")
        sys.exit(1)
    
    input_path = sys.argv[1]
    path = Path(input_path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {input_path}")
        sys.exit(1)
    
    logger.info(f"CodeAnnotator - Processing: {input_path}")
    
    annotator = CodeAnnotator()
    result = await annotator.run(str(path))
    
    if result:
        logger.info(f"\n{'='*60}")
        logger.info(f"SUCCESS: Annotation complete!")
        logger.info(f"Output: {result}")
        logger.info(f"{'='*60}")
        
        if path.is_file():
            annotated_file = Path(result)
            if annotated_file.exists():
                logger.info(f"\nAnnotated file preview (first 800 chars):")
                logger.info(f"{'-'*60}")
                content = annotated_file.read_text(encoding='utf-8')
                logger.info(content[:800])
                if len(content) > 800:
                    logger.info("...")
                logger.info(f"{'-'*60}")
    else:
        logger.error(f"Failed to annotate: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
