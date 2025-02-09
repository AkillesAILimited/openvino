// Copyright (C) 2018-2021 Intel Corporation
// SPDX-License-Identifier: Apache-2.0
//

#include "engines_util/execute_tools.hpp"
#include "gtest/gtest.h"
#include "ngraph/ngraph.hpp"
#include "ngraph/runtime/tensor.hpp"
#include "runtime/backend.hpp"
#include "util/all_close.hpp"
#include "util/all_close_f.hpp"
#include "util/ndarray.hpp"
#include "util/test_control.hpp"

NGRAPH_SUPPRESS_DEPRECATED_START

using namespace std;
using namespace ngraph;

static string s_manifest = "${MANIFEST}";

NGRAPH_TEST(${BACKEND_NAME}, round_half_to_even) {
    Shape shape{5};
    auto A = make_shared<op::Parameter>(element::f32, shape);
    auto f = make_shared<Function>(make_shared<op::v5::Round>(A, op::v5::Round::RoundMode::HALF_TO_EVEN),
                                   ParameterVector{A});

    auto backend = runtime::Backend::create("${BACKEND_NAME}");

    auto a = backend->create_tensor(element::f32, shape);
    copy_data(a, vector<float>{0.9f, 2.5f, 2.3f, 1.5f, -4.5f});
    auto result = backend->create_tensor(element::f32, shape);

    auto handle = backend->compile(f);
    handle->call_with_validate({result}, {a});
    EXPECT_TRUE(test::all_close_f((vector<float>{1.0f, 2.0f, 2.0f, 2.0f, -4.0f}),
                                  read_vector<float>(result),
                                  MIN_FLOAT_TOLERANCE_BITS));
}

NGRAPH_TEST(${BACKEND_NAME}, round_away_from_zero) {
    Shape shape{5};
    auto A = make_shared<op::Parameter>(element::f32, shape);
    auto f = make_shared<Function>(make_shared<op::v5::Round>(A, op::v5::Round::RoundMode::HALF_AWAY_FROM_ZERO),
                                   ParameterVector{A});

    auto backend = runtime::Backend::create("${BACKEND_NAME}");

    auto a = backend->create_tensor(element::f32, shape);
    copy_data(a, vector<float>{0.9f, 2.5f, 2.3f, 1.5f, -4.5f});
    auto result = backend->create_tensor(element::f32, shape);

    auto handle = backend->compile(f);
    handle->call_with_validate({result}, {a});
    EXPECT_TRUE(test::all_close_f((vector<float>{1.0f, 3.0f, 2.0f, 2.0f, -5.0f}),
                                  read_vector<float>(result),
                                  MIN_FLOAT_TOLERANCE_BITS));
}

NGRAPH_TEST(${BACKEND_NAME}, round_2D) {
    Shape shape{3, 5};
    auto A = make_shared<op::Parameter>(element::f32, shape);
    auto f = make_shared<Function>(make_shared<op::v5::Round>(A, op::v5::Round::RoundMode::HALF_TO_EVEN),
                                   ParameterVector{A});

    auto backend = runtime::Backend::create("${BACKEND_NAME}");

    auto a = backend->create_tensor(element::f32, shape);
    copy_data(
        a,
        vector<float>{0.1f, 0.5f, 0.9f, 1.2f, 1.5f, 1.8f, 2.3f, 2.5f, 2.7f, -1.1f, -1.5f, -1.9f, -2.2f, -2.5f, -2.8f});
    auto result = backend->create_tensor(element::f32, shape);

    auto handle = backend->compile(f);
    handle->call_with_validate({result}, {a});
    EXPECT_TRUE(test::all_close_f(
        (vector<float>{0.f, 0.f, 1.f, 1.f, 2.f, 2.f, 2.f, 2.f, 3.f, -1.f, -2.f, -2.f, -2.f, -2.f, -3.f}),
        read_vector<float>(result),
        MIN_FLOAT_TOLERANCE_BITS));
}

NGRAPH_TEST(${BACKEND_NAME}, round_int64) {
    // This tests large numbers that will not fit in a double
    Shape shape{3};
    auto A = make_shared<op::Parameter>(element::i64, shape);
    auto f = make_shared<Function>(make_shared<op::v5::Round>(A, op::v5::Round::RoundMode::HALF_TO_EVEN),
                                   ParameterVector{A});

    auto backend = runtime::Backend::create("${BACKEND_NAME}");

    auto a = backend->create_tensor(element::i64, shape);
    vector<int64_t> expected{0, 1, 0x4000000000000001};
    copy_data(a, expected);
    auto result = backend->create_tensor(element::i64, shape);

    auto handle = backend->compile(f);
    handle->call_with_validate({result}, {a});
    EXPECT_EQ(expected, read_vector<int64_t>(result));
}
