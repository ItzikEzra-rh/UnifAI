const SETTINGS_KEYWORDS = [
  "Library",
  "Resource",
  "Variables",
  "Documentation",
  "Metadata",
  "Suite Setup",
  "Suite Teardown",
  "Force Tags",
  "Default Tags",
  "Test Setup",
  "Test Teardown",
  "Test Template",
  "Test Timeout",
  "Task Setup",
  "Task Teardown",
  "Task Template",
  "Task Timeout",
];

function caseInsensitive(keyword) {
  return new RegExp(
    keyword
      .split("")
      .map(letter => `[${letter.toLowerCase()}${letter.toUpperCase()}]`)
      .join("")
  );
}

function section_header($, name) {
  return seq(
    alias(
      token(seq("***", optional(" "), caseInsensitive(name), optional(" "), "***")),
      $.section_header
    ),
    optional(alias(/[^\r\n]+/, $.extra_text)),
    $._line_break
  );
}

function setting(name) {
  return token(seq("[", optional(" "), caseInsensitive(name), optional(" "), "]"));
}

module.exports = grammar({
  name: "robot",

  extras: $ => [$.comment],

  conflicts: $ => [
    [$.keyword_invocation],
    [$.variable_assignment],
    [$.arguments],
    [$.continuation],
    [$.block],
    [$.except_statement],
    [$.except_statement, $.continuation],
    [$.finally_statement],
  ],

  rules: {
    source_file: $ => seq(
      optional(/\s+/), // Allows whitespace before the first section
      repeat($.section)
    ),

    section: $ => choice(
      $.settings_section,
      $.variables_section,
      $.keywords_section,
      $.test_cases_section,
    ),

    // Settings section
        settings_section: $ => seq(
          section_header($, "Settings"),
          repeat(choice(
                $.setting_statement,
                $.ignored_setting,  // Ignore any setting that starts with Suite or Test
                $._empty_line,
          )),
        ),
    setting_statement: $ => seq(
      choice(...SETTINGS_KEYWORDS.map(caseInsensitive)),
      $.arguments,
      $._line_break,
    ),
        ignored_setting: $ => seq(
          choice(
                /Suite\s+\S+/,
                /Test\s+\S+/
          ),
          /.*/,  // Skip the rest of the line
          $._line_break
        ),
    // Variables section
    variables_section: $ => seq(
      section_header($, "Variables"),
      repeat(choice($.variable_definition, $._empty_line)),
    ),
    variable_definition: $ => seq(
      choice(
        seq("${", $.variable_name, "}"),
        seq("@{", $.variable_name, "}"),
        seq("&{", $.variable_name, "}")
      ),
      optional(choice("=", " =")),
      optional($.arguments),
      $._line_break,
    ),

    // Keywords section
    keywords_section: $ => seq(
      section_header($, "Keywords"),
      repeat(choice($.keyword_definition, $._empty_line)),
    ),
    keyword_definition: $ => seq(
      alias($.text_chunk, $.name),
      $._line_break,
      alias($.keyword_definition_body, $.body),
    ),
    keyword_definition_body: $ => prec.right(repeat1(
      choice(
        seq($._indentation, $.keyword_setting, $._line_break),
        seq($._indentation, $.statement, $._line_break),
        $._empty_line,
      )
    )),
    keyword_setting: $ => prec.right(seq(
      choice(
        seq(setting("Documentation"), optional($.arguments), optional($._line_break)),
        seq(setting("Tags"), $.arguments, $._line_break),
        seq(setting("Arguments"), optional($.arguments), $._line_break),
        seq(setting("Return"), $.arguments, $._line_break),
        seq(setting("Teardown"), $.arguments, $._line_break),
        seq(setting("Timeout"), $.arguments, $._line_break),
      ),
      optional($.arguments),
    )),

    // Test cases / Tasks section
    test_cases_section: $ => seq(
      section_header($, "Test Cases"),
      repeat(choice($.test_case_definition, $._empty_line)),
    ),
    test_case_definition: $ => seq(
      alias($.text_chunk, $.name),
      choice(
        seq(alias($.arguments_without_continuation, $.arguments), $._line_break),
        seq($._line_break, alias($.test_case_definition_body, $.body))
      )
    ),
    test_case_definition_body: $ => prec.right(repeat1(
      choice(
        seq($._indentation, $.test_case_setting, $._line_break),
        seq($._indentation, $.statement, $._line_break),
        $._empty_line,
      )
    )),
    test_case_setting: $ => seq(
      choice(
        setting("Documentation"),
        setting("Tags"),
        setting("Setup"),
        setting("Teardown"),
        setting("Template"),
        setting("Timeout"),
      ),
      $.arguments,
    ),

    // Statements
    statement: $ => seq(
      choice(
        $.variable_assignment,
        $.keyword_invocation,
        $.return_statement,
        $.if_statement,
        $.inline_if_statement,
        $.try_statement,
        $.while_statement,
        $.for_statement,
        $.continue_statement,
        $.break_statement,
      ),
    ),

    // Return statement
    return_statement: $ => prec.right(seq(
      "RETURN",
      optional(seq($._separator, alias($.argument, $.return_value)))
    )),

        variable_assignment: $ => seq(
          choice(
                seq("${", $.variable_name, "}"),  // Scalar variable
                seq("@{", $.variable_name, "}"),  // List variable
                seq("&{", $.variable_name, "}")   // Dictionary variable
          ),
          optional(choice("=", " =")),  // Allow both `=` and `=` assignment operators
          optional($.arguments),  // Arguments after the assignment
        ),

    keyword_invocation: $ => seq(
      alias($.text_chunk, $.keyword),
      optional($.arguments),
    ),

    // If / Else / Try statements
    if_statement: $ => seq(
      "IF",
      $._separator,
      field("condition", $.argument),
      $._line_break,
      optional(field("consequence", $.block)),
      repeat(field("alternative", $.elseif_statement)),
      optional(field("alternative", $.else_statement)),
      seq($._indentation, "END"),
    ),

    elseif_statement: $ => prec.dynamic(100, seq(
      $._indentation, "ELSE IF", $._separator, field("condition", $.argument), $._line_break, field("consequence", $.block)
    )),

    else_statement: $ => prec.dynamic(100, seq($._indentation, "ELSE", $._line_break, field("consequence", $.block))),

    inline_if_statement: $ => seq(
      "IF",
      $._separator,
      $.argument,
      optional( seq(
              $._line_break,
              $.indented_ellipses,
      )),
      $._separator,
      $.inline_statement,
      repeat(seq($._separator, $.inline_elseif_statement)),
      optional(seq($._separator, $.inline_else_statement)),
    ),

    block: $ => repeat1(choice($._empty_line, seq($._indentation, $.statement, $._line_break))),

    inline_elseif_statement: $ => prec.dynamic(100, seq("ELSE IF", $._separator, $.argument, $._separator, $.inline_statement)),
    inline_else_statement: $ => prec.dynamic(100, seq("ELSE", $._separator, $.inline_statement)),

    inline_statement: $ => seq(choice($.variable_assignment, $.keyword_invocation, $.return_statement)),

    try_statement: $ => seq(
      "TRY",
      $._line_break,
      optional($.block),
      repeat($.except_statement),
      prec.dynamic(200, optional($.else_statement)),
      optional($.finally_statement),
      $._indentation, "END"
    ),

    except_statement: $ => prec.dynamic(100, seq($._indentation, "EXCEPT", optional($.arguments), $._line_break, optional($.block))),

    finally_statement: $ => prec.dynamic(100, seq($._indentation, "FINALLY", $._line_break, optional($.block))),

    // While / For statements
    while_statement: $ => seq(
      "WHILE",
      field("condition", alias($.arguments_without_continuation, $.arguments)),
      $._line_break,
      field("body", optional($.block)),
      $._indentation, "END"
    ),

    for_statement: $ => seq(
      "FOR",
      field("left", alias(repeat1(seq($._separator, $.scalar_variable)), $.variable_list)),
      $._separator,
      field("right", choice(
        alias($._for_in, $.in),
        alias($._for_in_range, $.in_range),
        alias($._for_in_enumerate, $.in_enumerate),
        alias($._for_in_zip, $.in_zip),
      )),
      $._line_break,
      field("body", $.block),
      $._indentation, "END"
    ),

    _for_in: $ => seq(seq("IN", $.arguments)),

    _for_in_range: $ => seq(
      "IN RANGE",
      $._separator,
      $.argument,
      optional(seq($._separator, $.argument, optional(seq($._separator, $.argument))))
    ),

    _for_in_enumerate: $ => seq("IN ENUMERATE", $.arguments),

    _for_in_zip: $ => seq("IN ZIP", $.arguments),

    continue_statement: $ => "CONTINUE",
    break_statement: $ => "BREAK",

    // Arguments
    arguments: $ => seq(
      repeat1(seq($._separator, choice($.argument, seq($.scalar_variable, "=", $.argument)))),
      repeat($.continuation)
    ),

    arguments_without_continuation: $ => repeat1(seq($._separator, $.argument)),

    continuation: $ => prec.dynamic(100, seq($._line_break, optional($._indentation), $.ellipses, repeat(seq($._separator, $.argument)))),

    ellipses: $ => "...",
    indented_ellipses: $ => token(seq(
      /[ ]{2}|\t/,
      optional(/[ \t]+/),
      "..."
    )),


    argument: $ => seq(
      choice($.text_chunk, $.scalar_variable, $.list_variable, $.dictionary_variable, $.inline_python_expression),
      repeat(seq(optional(" "), choice($.text_chunk, $.scalar_variable, $.inline_python_expression)))
    ),

    scalar_variable: $ => seq("${", optional(" "), $.variable_name, optional(" "), "}"),
    list_variable: $ => seq("@{", optional(" "), $.variable_name, optional(" "), "}"),
    dictionary_variable: $ => seq("&{", optional(" "), $.variable_name, optional(" "), "}"),

    inline_python_expression: $ => prec.left(seq("${{", alias(repeat(choice("}", /[^\r\n}]+/)), $.python_expression), "}}")),

    variable_name: $ => /[^{}]+/,

    text_chunk: $ => token(seq(
      choice(/[^\s$@&{#]/, /[$@&][^{]/, /[^$@&]\{/),
      repeat(choice(/[^\s$@&{]/, /[$@&][^{]/, /[^$@&]\{/)),
      repeat(seq(" ", repeat1(choice(/[^\s$@&{]/, /[$@&][^{]/, /[^$@&]\{/))))
    )),

    comment: $ => token(seq(optional(/[ \t]+/), "#", /[^\n]*/)),

    _separator: $ => token(seq(/[ ]{2}|\t/, optional(/[ \t]+/))),
    _indentation: $ => $._separator,

    _line_break: $ => /\s*(\r?\n)/,

    _empty_line: $ => seq(optional(/[ \t]+/), $._line_break),
  },
});
