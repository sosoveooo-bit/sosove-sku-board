"""Synthetic source-only COD commerce contracts; no backend, storage or network."""

import unittest

from sku_board.cod_content import promotion_contract, review_quotes


class CodPromotionContractTests(unittest.TestCase):
    def assert_offer(self, source: str, percent: int | float, *, maximum: bool = False) -> dict:
        contract = promotion_contract(source)
        self.assertEqual(contract.get("percent"), percent, source)
        self.assertEqual(contract.get("isMaximum"), maximum, source)
        self.assertEqual(contract.get("label"), f"{contract['percentText']}% OFF")
        self.assertTrue(contract.get("sourceText"))
        self.assertIn(contract["sourceText"], source)
        return contract

    def test_missing_source_does_not_create_an_offer(self) -> None:
        for source in ("", "添加促销页", "做一个折扣徽章", "面料含棉70%，产品轻便", "不要显示价格", None):
            with self.subTest(source=source):
                self.assertEqual(promotion_contract(source), {})

    def test_arbitrary_explicit_percentages_are_preserved(self) -> None:
        for source, percent in (
            ("促销优惠15%", 15), ("折扣：25%", 25),
            ("Sale discount 33.5%", 33.5), ("SALE 0.1% OFF", 0.1),
            ("100% OFF", 100), ("Sale discount 33.50%", 33.5),
        ):
            with self.subTest(source=source):
                self.assert_offer(source, percent)

    def test_japanese_english_korean_and_full_width_percentage_sources(self) -> None:
        for source, percent in (
            ("20%OFF", 20), ("Sale discount 15%", 15),
            ("할인15%", 15), ("15% 할인", 15),
            ("２０％ＯＦＦ", 20), ("割引：25％", 25),
        ):
            with self.subTest(source=source):
                self.assert_offer(source, percent)

    def test_chinese_zhe_means_fraction_of_original_price(self) -> None:
        for source, percent in (
            ("活动打8折", 20), ("全场8.5折", 15),
            ("优惠八折", 20), ("打九五折", 5),
            ("限量商品0折", 100),
        ):
            with self.subTest(source=source):
                result = self.assert_offer(source, percent)
                self.assertEqual(result["sourceType"], "chinese_zhe")

    def test_non_discount_fold_words_do_not_create_an_offer(self) -> None:
        for source in ("使用三折页宣传单", "8折叠结构", "这款折叠椅有8种角度"):
            with self.subTest(source=source):
                self.assertEqual(promotion_contract(source), {})

    def test_explicit_promotion_exclusion_wins_over_numeric_offer(self) -> None:
        for source in (
            "优惠25%。不要促销", "不显示折扣，商品原本有20%OFF", "不要折扣图。Sale discount 15%",
            "无折扣。原先20%OFF", "促销：无；原先25%OFF",
            "NO DISCOUNT. 20% OFF", "Do not show promotions; Sale discount 15%",
            "20%OFF\n割引なし", "할인15%\n할인 표시하지 마세요",
        ):
            with self.subTest(source=source):
                self.assertEqual(promotion_contract(source), {})

    def test_excluding_price_does_not_exclude_discount(self) -> None:
        for source in (
            "不要价格，优惠15%", "不显示售价；打8.5折", "No price. 15% OFF",
            "Do not show the product price. Sale discount 15%",
        ):
            with self.subTest(source=source):
                self.assert_offer(source, 15)

    def test_invalid_percentages_do_not_fall_back_or_match_a_numeric_suffix(self) -> None:
        for source in ("0% OFF", "Sale discount -15%", "150%OFF", "101%OFF", "Sale discount 100.1%", "10折", "打12折"):
            with self.subTest(source=source):
                self.assertEqual(promotion_contract(source), {})

    def test_source_qualifier_and_conflicting_offers_are_not_invented_or_collapsed(self) -> None:
        self.assert_offer("Up to 25% OFF", 25, maximum=True)
        self.assert_offer("最大20％OFF", 20, maximum=True)
        self.assert_offer("最多优惠33.5%", 33.5, maximum=True)
        self.assert_offer("优惠20%\n20%OFF", 20)
        self.assertEqual(promotion_contract("会员15%OFF，普通用户10%OFF"), {})

    def test_documentation_examples_do_not_become_live_offers(self) -> None:
        for source in (
            "折扣字段尚未提供，例如50% OFF只是样例", "示例折扣：20%OFF",
            "Promotion is pending. For example: 25% OFF", "50%OFF仅为示例",
        ):
            with self.subTest(source=source):
                self.assertEqual(promotion_contract(source), {})
        self.assert_offer("优惠20%OFF，例如适用于厨房用品", 20)


class CodReviewQuoteTests(unittest.TestCase):
    def test_request_for_reviews_is_not_review_data(self) -> None:
        for source in (
            "", None, "添加好评页", "写4条好评", "Add four positive customer reviews",
            "用户评价：添加4条好评", "真实评价：\n1. 请生成一条耐用好评\n2. 写一个顾客评论",
            "Customer reviews: Generate four positive reviews", "用户评价：暂无，稍后提供",
            "用户评价：请根据商品卖点生成四条真实感反馈",
        ):
            with self.subTest(source=source):
                self.assertEqual(review_quotes(source), [])

    def test_explicit_source_section_returns_only_actual_numbered_quotes(self) -> None:
        source = "产品卖点：轻便\n真实评价：\n1. “握持很方便。”\n2. 「洗起来很省事！」\n商品规格：\n1. 长度20cm"
        self.assertEqual(review_quotes(source), ["握持很方便。", "洗起来很省事！"])

    def test_customer_review_section_preserves_verbatim_content_and_count(self) -> None:
        source = 'Customer reviews:\n- "It is sturdy, and I use it every day."\n- "Easy to clean!"\nPromotion: 15% OFF'
        self.assertEqual(review_quotes(source), ["It is sturdy, and I use it every day.", "Easy to clean!"])

    def test_one_supplied_review_is_not_expanded_to_four(self) -> None:
        self.assertEqual(review_quotes('用户评价：「很适合日常使用。」'), ["很适合日常使用。"])
        self.assertEqual(review_quotes("用户评价：\n1. 握持方便，清洗也省事。"), ["握持方便，清洗也省事。"])

    def test_inline_quotes_and_markdown_data_headings(self) -> None:
        self.assertEqual(review_quotes('**真实评价**："好用。"；「方便收纳。」'), ["好用。", "方便收纳。"])
        self.assertEqual(review_quotes('### Customer reviews\n1) "Works well."'), ["Works well."])

    def test_review_text_outside_a_marked_source_section_is_not_consumed(self) -> None:
        self.assertEqual(review_quotes('这张图写“好用又省事”，并添加四条顾客感受。'), [])
        self.assertEqual(review_quotes('Product benefits:\n- "Very useful"\n- "Good value"'), [])

    def test_blank_boundary_does_not_turn_later_unmarked_product_prose_into_reviews(self) -> None:
        source = 'Customer reviews:\n- "Good grip."\n\nThe product has a stainless-steel handle.'
        self.assertEqual(review_quotes(source), ["Good grip."])

    def test_inner_quotes_and_contractions_are_preserved(self) -> None:
        source = 'Customer reviews:\n1. It\'s a "great" everyday tool.\n2. “The finish feels nice.”'
        self.assertEqual(review_quotes(source), ['It\'s a "great" everyday tool.', "The finish feels nice."])

    def test_quote_attribution_is_not_mixed_into_the_quote(self) -> None:
        self.assertEqual(review_quotes('真实评价：\n1. 客户A：“手柄握着很顺手。”'), ["手柄握着很顺手。"])

    def test_separate_data_blocks_keep_source_order_without_filling_missing_rows(self) -> None:
        source = '真实评价：\n1. “第一条。”\n限制：不要价格\nCustomer reviews:\n- "Second quote."'
        self.assertEqual(review_quotes(source), ["第一条。", "Second quote."])

    def test_quoted_and_parenthesized_placeholders_are_not_reviews(self) -> None:
        for source in ('真实用户评价："暂无"', "用户评价\n（待补充）", 'Customer reviews: "N/A"', '真实评价：客户A：“”'):
            with self.subTest(source=source):
                self.assertEqual(review_quotes(source), [])
        self.assertEqual(review_quotes('真实评价："很好用。"；"暂无"'), ["很好用。"])

    def test_real_quotes_starting_with_negative_words_are_retained(self) -> None:
        self.assertEqual(review_quotes("真实评价：\n1. 无异味，握着舒服。\n2. 暂无问题，清洗方便。"), ["无异味，握着舒服。", "暂无问题，清洗方便。"])
        self.assertEqual(review_quotes("Customer reviews:\n1. None of the parts feel loose."), ["None of the parts feel loose."])


if __name__ == "__main__":
    unittest.main()
