## Foundations & Principles

The project's approach to annotating is AST-based transformation; 

We offer both inline and stub-based annotation generation, whose mechanics, both shared and individual, have been split into AST transformers.
By reading in files that have been traced, which are stored in the ['Filename' column of the trace data](tracing.md#api), trace data can be collected on a per-file basis and applied appropriately.
Specifically, from this per-file basis trace data, annotations (also called type hints) can be generated for each file using the aforementioned transformers, and output appropriately.


But first, the trace data must be cleaned and appropriately unified.
To this extent, unifiers with a common interface have been implemented to cover unification (read filtering and reducing) needs.


## Unifiers


TODO: Add motivation, functionality and example for every unifier

### Filtering


#### Drop Duplication



#### Min-Threshold




### Reducing

#### Subtypes


#### Unions



## Annotations

### Transformers


#### 


### Inline Annotation Generation

If the trace data does not contain a type hint, but the original has an annotation, this can be retained by doing XXX.


### Bonus: Stub File Generation


## Unifier API


## Annotation Generation API