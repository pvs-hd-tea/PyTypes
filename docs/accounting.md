- Result: 55% Ben, 45% Viet
    - Common: 80% Ben, 20% Viet - 200LOC
        - data_file_collector.py: 100% Viet
        - ptconfig.py & resolver.py: 100% Ben
        - trace_data_category.py: 50% Viet, 50% Ben

    - Fetching: 75% Ben, 25% Viet - 450LOC
        - API for fetching different repository formats, updated CST-based implemention of decorator appending by Ben
        - Original implementation of `AppendDecoratorTransformer` and fetching mode of evaluation by Viet

    - Tracing: 70% Ben, 30% Viet - 700LOC
        - trace_update.py: `BatchTraceUpdate` and `TraceUpdate`: 100% Ben
        - tracer.py: 50% Ben, 50% Viet
            - Initial Implementation by Viet: 
                - `LOCAL_VARIABLES`, `FUNCTION_PARAMETER`, `FUNCTION_RETURN` +
                - later implementation of `CLASS_MEMBERS` 
                - TracerBase refactor

            - Later updates by Ben: 
                - `GLOBAL_VARIABLE`
                - introduction of `Resolver` 
                - Batch Updates 
                - Schema Refactor

        - Optimisation: 100% Ben

        - decorators.py: 80% Ben, 20% Viet
            - Initial implementation of `@entrypoint` and `@register` by Ben
            - Benchmarking mode by Viet 
            - Refactor into singular decorator to support pytest features + error logging by Ben

    - Typegen: 60% Ben, 40% Viet - 1000LOC
        - Unification: 25% Ben, 75% Viet
            - DropDuplicatesFilter, MinThresholdFilter, DropVariablesOfMultipleTypesFilter, DropTestFunctionDataFilter, KeepOnlyFirstFilter, Initial Implementation of UnifySubTypesFilter, TraceDataFilter & TraceDataFilterList by Viet
            - Implementation of UnionFilter and refactoring + bugfixing in UnifySubTypesFilter + Resolver usage by Ben

        - Annotation Generation 75% Ben, 25% Viet:
            - RemoveTypeHintsTransformer, ImportUnionTransformer, Initial implementation of EvaluationInlineGenerator & StubFileGenerator by Viet

            - TypeHintTransformer, AddImportTransformer, InlineGenerator and base class TypeHintGenerator API design by Ben
            - Refactoring of mypy.stubgen usage into a Transformer also by Ben

        - TraceDataFileCollector: 100% Viet

    - Evaluation: 100% Viet - 700LOC


- Responsibilites of bugfixing were evenly shared
- Refactoring was primilarily performed by Ben
- Quality of testing was primarily down to Viet
- Viet was very meticulous when it came to reviewing PRs

