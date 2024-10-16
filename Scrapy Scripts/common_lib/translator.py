import re
import json
import requests

# Clean text from unusual characters
def clean_text(text):
    # Removing encoded characters like \xe2\x80\x9c etc.
    cleaned_text = re.sub(r'\\x[0-9A-Fa-f]{2}', '', text)
    
    # Removing unnecessary backslashes and other artifacts
    cleaned_text = re.sub(r'\\', '', cleaned_text)
    
    return cleaned_text

def translate_to_english(source_lang="auto", target_lang="en", message="") -> str:
    try:
        with requests.get(
                f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={message}") as response:
            data = json.loads(response.text)
            data = data[0]

            desc = ""

            for text in data:
                desc += text[0]
        return desc
    except:
        return ""
    
# # Translation function using AWS Translate
# def TRANSLATE(text, source="auto", target='en'):
#     # Create the AWS Translate client
#     translate = create_translate_client()
    
#     try:
#         # Call the translate API
#         response = translate.translate_text(
#             Text=text,
#             SourceLanguageCode=source,  # Example: 'ja' for Japanese
#             TargetLanguageCode=target  # Example: 'en' for English
#         )
        
#         # Clean and return the translated text
#         translated_text = response['TranslatedText']
#         return clean_text(translated_text)
    
#     except Exception as e:
#         print(f"Error translating text: {str(e)}")
#         input()
#         return ''

# def TRANSLATE(text, source="auto", target='en'):
#     return f'Translate: {source.lower()}\n{text}'

from deep_translator import GoogleTranslator
def TRANSLATE(text, source="auto", target='en'):
    return GoogleTranslator(source=source, target=target).translate(text)

from urllib.parse import quote
def TRANSLATE2(text, source="auto", target='en'):
    def clean_string(input_string):
        # Remove non-UTF-8 characters
        return re.sub(r'[^\x00-\x7F]+', '', input_string)

    if text:

        translatedMessage = ''
        for line in text.split('\n'):
            try:
                translatedMessage += translate_to_english(message=quote(line),source_lang=source,target_lang=target) + '\n'
            except:
                pass
        text = translatedMessage

    return clean_string(text.strip())

if __name__ == '__main__':
    # Example usage
    japanese_text = '''グ易イマ憶ぇゔべテれレ佳'''
    translated_text = TRANSLATE(japanese_text, 'ja', 'en')

    if translated_text:
        print(f"Translated Text: {translated_text}")
