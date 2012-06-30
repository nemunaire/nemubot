# coding=utf-8

import module_states_file as xmlparser

from .Question import Question

class QuestionFile:
  def __init__(self, filename):
    self.questions = xmlparser.parse_file(filename)
    self.questions.setIndex("xml:id")

  def getQuestion(self, ident):
    if ident in self.questions.index:
      return Question(self.questions.index[ident])
    else:
      return None
