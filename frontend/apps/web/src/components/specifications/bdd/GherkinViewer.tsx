import type { editor } from 'monaco-editor';

import { Editor } from '@monaco-editor/react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useCallback, useMemo, useState, type JSX } from 'react';

import { Badge, Button, Card, cn } from '@tracertm/ui';

import { StepBadge, type StepType } from './StepBadge';

interface GherkinViewerProps {
  content: string;
  className?: string;
  height?: string;
  collapsible?: boolean;
  showLineNumbers?: boolean;
}

interface ParsedGherkin {
  feature?: string;
  background?: string[];
  scenarios: {
    type: 'Scenario' | 'Scenario Outline';
    title: string;
    steps: {
      keyword: StepType;
      text: string;
    }[];
    examples?: string;
  }[];
}

const STEP_KEYWORDS: readonly StepType[] = ['Given', 'When', 'Then', 'And', 'But'];

const isStepKeyword = (value: string): value is StepType =>
  STEP_KEYWORDS.includes(value as StepType);

const isStepLine = (line: string): boolean => STEP_KEYWORDS.some((keyword) => line.startsWith(keyword));

const isScenarioLine = (line: string): boolean =>
  line.startsWith('Scenario:') || line.startsWith('Scenario Outline:');

const getScenarioKey = (scenario: ParsedGherkin['scenarios'][number]): string =>
  `${scenario.type}:${scenario.title}`;

const getScenarioStepKey = (
  scenarioKey: string,
  step: ParsedGherkin['scenarios'][number]['steps'][number],
): string => `${scenarioKey}:${step.keyword}:${step.text}`;

const getBackgroundStepKey = (step: string): string => {
  const keyword = step.split(/\s+/)[0] ?? 'step';
  return `${keyword}:${step}`;
};

const buildEditorOptions = (
  showLineNumbers: boolean,
): editor.IStandaloneEditorConstructionOptions => ({
  fontFamily: "'JetBrains Mono','Fira Code',monospace",
  fontSize: 13,
  lineNumbers: showLineNumbers ? 'on' : 'off',
  minimap: { enabled: false },
  padding: { bottom: 16, top: 16 },
  readOnly: true,
  renderLineHighlight: 'none',
  scrollBeyondLastLine: false,
});

function parseStepLine(line: string): { keyword: StepType; text: string } | null {
  const keyword = line.split(/\s+/)[0] ?? '';
  if (!isStepKeyword(keyword)) {
    return null;
  }

  return {
    keyword,
    text: line.slice(keyword.length).trim(),
  };
}

function createScenario(line: string): ParsedGherkin['scenarios'][number] {
  const isOutline = line.startsWith('Scenario Outline:');
  return {
    steps: [],
    title: line.replace('Scenario Outline:', '').replace('Scenario:', '').trim(),
    type: isOutline ? 'Scenario Outline' : 'Scenario',
  };
}

function parseGherkin(content: string): ParsedGherkin {
  const result: ParsedGherkin = { scenarios: [] };
  const lines = content.split('\n');

  let currentScenario: (typeof result.scenarios)[0] | null = null;
  let inBackground = false;
  const background: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }

    if (trimmed.startsWith('Feature:')) {
      result.feature = trimmed.replace('Feature:', '').trim();
      continue;
    }

    if (trimmed.startsWith('Background:')) {
      inBackground = true;
      continue;
    }

    if (inBackground) {
      if (isScenarioLine(trimmed)) {
        inBackground = false;
        result.background = background;
      }

      if (isStepLine(trimmed)) {
        background.push(trimmed);
        continue;
      }
    }

    if (isScenarioLine(trimmed)) {
      if (currentScenario) {
        result.scenarios.push(currentScenario);
      }
      currentScenario = createScenario(trimmed);
      continue;
    }

    if (currentScenario && isStepLine(trimmed)) {
      const step = parseStepLine(trimmed);
      if (step) {
        currentScenario.steps.push(step);
      }
      continue;
    }

    if (trimmed.startsWith('Examples:') && currentScenario) {
      currentScenario.examples = trimmed;
    }
  }

  if (currentScenario) {
    result.scenarios.push(currentScenario);
  }

  return result;
}

function RawGherkinCard({
  className,
  content,
  editorOptions,
  height,
}: {
  className?: string;
  content: string;
  editorOptions: editor.IStandaloneEditorConstructionOptions;
  height: string;
}): JSX.Element {
  return (
    <Card className={cn('border-border/50 overflow-hidden border', className)}>
      <Editor
        height={height}
        defaultLanguage='gherkin'
        value={content}
        theme='vs-dark'
        options={editorOptions}
      />
    </Card>
  );
}

function BackgroundSection({ steps }: { steps: readonly string[] }): JSX.Element {
  return (
    <Card className='border-border/50 bg-muted/30 border p-4'>
      <div className='space-y-3'>
        <h3 className='flex items-center gap-2 text-sm font-semibold'>
          <Badge variant='secondary'>Background</Badge>
        </h3>
        <div className='space-y-2'>
          {steps.map((step) => {
            const parsedStep = parseStepLine(step);
            if (parsedStep === null) {
              return null;
            }

            return (
              <div key={getBackgroundStepKey(step)} className='flex items-start gap-3'>
                <StepBadge type={parsedStep.keyword} compact />
                <span className='text-muted-foreground text-sm'>{parsedStep.text}</span>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}

function ScenarioSection({
  collapsible,
  index,
  isExpanded,
  toggleScenario,
  scenario,
}: {
  collapsible: boolean;
  index: number;
  isExpanded: boolean;
  toggleScenario: (index: number) => void;
  scenario: ParsedGherkin['scenarios'][number];
}): JSX.Element {
  const scenarioKey = getScenarioKey(scenario);
  const handleToggle = useCallback((): void => {
    toggleScenario(index);
  }, [index, toggleScenario]);

  return (
    <Card className='border-border/50 hover:border-primary/30 overflow-hidden border transition-colors'>
      {collapsible ? (
        <button
          className='hover:bg-muted/30 flex w-full items-center justify-between px-4 py-3 text-left transition-colors'
          onClick={handleToggle}
          type='button'
        >
          <div className='flex min-w-0 flex-1 items-center gap-3'>
            {isExpanded ? (
              <ChevronDown className='text-muted-foreground h-4 w-4 flex-shrink-0' />
            ) : (
              <ChevronRight className='text-muted-foreground h-4 w-4 flex-shrink-0' />
            )}
            <Badge variant='outline' className='font-mono text-xs'>
              {scenario.type === 'Scenario Outline' ? 'Outline' : 'Scenario'}
            </Badge>
            <h4 className='truncate text-sm font-semibold'>{scenario.title}</h4>
          </div>
          <Badge variant='secondary' className='ml-2 text-xs'>
            {scenario.steps.length} steps
          </Badge>
        </button>
      ) : (
        <div className='bg-muted/20 flex items-center justify-between px-4 py-3'>
          <div className='flex min-w-0 flex-1 items-center gap-3'>
            <Badge variant='outline' className='font-mono text-xs'>
              {scenario.type === 'Scenario Outline' ? 'Outline' : 'Scenario'}
            </Badge>
            <h4 className='truncate text-sm font-semibold'>{scenario.title}</h4>
          </div>
          <Badge variant='secondary' className='ml-2 text-xs'>
            {scenario.steps.length} steps
          </Badge>
        </div>
      )}

      {(!collapsible || isExpanded) && (
        <div className='border-border/50 bg-background space-y-3 border-t px-4 py-4'>
          <div className='space-y-2'>
            {scenario.steps.map((step) => (
              <div
                key={getScenarioStepKey(scenarioKey, step)}
                className='hover:bg-muted/30 flex items-start gap-3 rounded p-2 transition-colors'
              >
                <StepBadge type={step.keyword} compact />
                <span className='text-muted-foreground flex-1 text-sm leading-relaxed'>
                  {step.text}
                </span>
              </div>
            ))}
          </div>

          {scenario.examples && (
            <div className='border-border/50 border-t pt-2'>
              <Button variant='outline' size='sm' className='h-7 text-xs' type='button'>
                {scenario.examples}
              </Button>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function GherkinViewer({
  content,
  className,
  height = '400px',
  collapsible = true,
  showLineNumbers = true,
}: GherkinViewerProps): JSX.Element {
  const [expandedScenarios, setExpandedScenarios] = useState<Set<number>>(new Set([0]));
  const parsed = useMemo(() => parseGherkin(content), [content]);
  const editorOptions = useMemo(() => buildEditorOptions(showLineNumbers), [showLineNumbers]);

  const toggleScenario = useCallback((index: number): void => {
    setExpandedScenarios((previous) => {
      const next = new Set(previous);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  if (!parsed.feature && parsed.scenarios.length === 0) {
    return (
      <RawGherkinCard
        className={className}
        content={content}
        editorOptions={editorOptions}
        height={height}
      />
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {parsed.feature && (
        <Card className='border-primary/20 bg-primary/5 border p-4'>
          <div className='space-y-2'>
            <Badge className='w-fit'>Feature</Badge>
            <h2 className='text-xl font-semibold'>{parsed.feature}</h2>
          </div>
        </Card>
      )}

      {parsed.background && parsed.background.length > 0 && <BackgroundSection steps={parsed.background} />}

      {parsed.scenarios.length > 0 && (
        <div className='space-y-2'>
          {parsed.scenarios.map((scenario, index) => (
            <ScenarioSection
              key={getScenarioKey(scenario)}
              collapsible={collapsible}
              index={index}
              isExpanded={expandedScenarios.has(index)}
              scenario={scenario}
              toggleScenario={toggleScenario}
            />
          ))}
        </div>
      )}

      {parsed.scenarios.length === 0 && !parsed.feature && (
        <RawGherkinCard content={content} editorOptions={editorOptions} height={height} />
      )}
    </div>
  );
}
